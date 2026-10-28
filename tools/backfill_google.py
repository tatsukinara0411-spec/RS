#!/usr/bin/env python3
"""
Googleマップの補完が止まっていた週（2026-09-14〜）の行を、後から代表電話番号・住所で補完する。

・対象：BACKFILL_TABS（カンマ区切り）のタブで、「Google照合」列がまだ空の行
・1回の実行で調べる社数は BACKFILL_MAX_LOOKUPS（既定 450。1社2回呼ぶので約900回＝1日の上限1,000回の内側）
・Googleが返した施設名が社名と一致したときだけ採用（utils/places.py と同じ照合）
・電話番号：Googleの代表番号があれば置き換える。無ければ求人ページの番号のまま
・住所：番地の無い住所（「東京都 新宿駅」など）だけGoogleの住所に置き換える
・処理した行は「Google照合」列に 代表番号／該当なし／対象外 を書く（次の実行では飛ばす）
・課金エラー・回数超過が出たらその場で止め、印は付けない（次回やり直す）
・タブの全行が終わったら、そのタブをKIZUNAの取込待ちへ送る（合言葉が無ければ送らない）
"""
import asyncio
import logging
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import gspread
from google.oauth2.service_account import Credentials

from models.lead import Lead
from storage.kizuna import push_to_kizuna
from utils.credentials import load_service_account_info
from utils.places import _find_place, _place_details, _is_match

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
MARK_HEADER = "Google照合"
NOT_COMPANY_RE = re.compile(r"^東京都|求人.*件|チェック|を見る|[、。！!]$|マッチした")
STOP_STATUSES = {"REQUEST_DENIED", "OVER_QUERY_LIMIT", "OVER_DAILY_LIMIT"}


def notice(title: str, msg: str) -> None:
    print(f"::notice title={title}::" + msg.replace("%", "%25").replace("\n", "%0A"))


def clean_name(s: str) -> str:
    s = (s or "").replace("他の店舗", "")
    return " ".join(s.split())


def col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


async def lookup(session, name, address, key):
    """(phone, address, status) を返す。status が STOP_STATUSES なら呼び出し側で止める。"""
    pid, pname, st, _ = await _find_place(session, name, address, key)
    if st in STOP_STATUSES:
        return "", "", st
    if not pid:
        return "", "", "NOT_FOUND"
    if not _is_match(name, pname):
        return "", "", "MISMATCH"
    phone, addr, st2, _ = await _place_details(session, pid, key)
    if st2 in STOP_STATUSES:
        return "", "", st2
    return phone, addr, "OK"


async def process_tab(ws, key, budget, stop_flag):
    values = ws.get_all_values()
    if not values:
        return 0, True, []
    header = values[0]
    idx = {h: i for i, h in enumerate(header)}
    need = ["屋号", "住所", "電話番号"]
    if any(h not in idx for h in need):
        logger.warning(f"[{ws.title}] 列の形式が違うため対象外: {header}")
        return 0, True, []
    if MARK_HEADER not in idx:
        mcol = len(header) + 1
        ws.update_cell(1, mcol, MARK_HEADER)
        idx[MARK_HEADER] = mcol - 1
    ci, ai, pi, mi = idx["屋号"], idx["住所"], idx["電話番号"], idx[MARK_HEADER]

    rows = values[1:]
    def cell(r, i):
        return r[i] if len(r) > i else ""
    todo = [(n + 2, r) for n, r in enumerate(rows) if not cell(r, mi).strip()]
    logger.info(f"[{ws.title}] 未照合 {len(todo)}件 / 全{len(rows)}件")

    updates, used = [], 0
    sem = asyncio.Semaphore(5)
    results = {}

    async def one(session, rownum, r):
        nonlocal used
        name = clean_name(cell(r, ci))
        addr = cell(r, ai)
        if not name or NOT_COMPANY_RE.search(name):
            results[rownum] = ("", "", "SKIP", addr)
            return
        async with sem:
            if stop_flag["stop"]:
                return
            await asyncio.sleep(0.15)
            try:
                phone, gaddr, st = await lookup(session, name, addr, key)
            except Exception as e:
                logger.debug(f"エラー {name}: {e}")
                phone, gaddr, st = "", "", "ERROR"
            if st in STOP_STATUSES:
                stop_flag["stop"] = True
                stop_flag["status"] = st
                return
            results[rownum] = (phone, gaddr, st, addr)

    batch = []
    for rownum, r in todo:
        name = clean_name(cell(r, ci))
        if name and not NOT_COMPANY_RE.search(name):
            if used >= budget:
                break
            used += 1
        batch.append((rownum, r))

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[one(session, n, r) for n, r in batch])

    found = 0
    for rownum, (phone, gaddr, st, addr) in results.items():
        if st == "ERROR":
            continue  # 一時的な失敗は印を付けず次回やり直す
        if phone:
            updates.append(gspread.Cell(rownum, pi + 1, phone))
            found += 1
        if gaddr and not re.search(r"\d", addr):
            updates.append(gspread.Cell(rownum, ai + 1, gaddr))
        mark = "代表番号" if phone else ("対象外" if st == "SKIP" else "該当なし")
        updates.append(gspread.Cell(rownum, mi + 1, mark))
    if updates:
        ws.update_cells(updates, value_input_option="USER_ENTERED")

    marked = sum(1 for v in results.values() if v[2] != "ERROR")
    complete = (len(todo) - marked) == 0
    logger.info(f"[{ws.title}] 今回 照合{marked}件（Google問い合わせ {used}社）・代表番号 {found}件・残り {len(todo) - marked}件")
    return used, complete, [ws.title, marked, found, len(todo) - marked]


def leads_from_tab(ws) -> list:
    values = ws.get_all_values()
    header = values[0]
    idx = {h: i for i, h in enumerate(header)}
    def g(r, h):
        i = idx.get(h)
        return r[i] if i is not None and len(r) > i else ""
    out = []
    for r in values[1:]:
        name = clean_name(g(r, "屋号"))
        if not name or NOT_COMPANY_RE.search(name):
            continue
        l = Lead(company_name=name, legal_name=g(r, "法人名"), corporate_number=g(r, "法人番号"),
                 address=g(r, "住所"), phone=g(r, "電話番号"), industry=g(r, "業種") or "",
                 source_site=g(r, "ソース") or "不明", collected_at=re.sub(r"T(\d):", r"T0\1:", g(r, "収集日時").replace(" ", "T")) if g(r, "収集日時") else "")
        l.phone_source = "google" if g(r, MARK_HEADER) == "代表番号" else ("listing" if l.phone else "")
        out.append(l)
    return out


def main():
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not key:
        print("GOOGLE_MAPS_API_KEY が未設定", file=sys.stderr)
        sys.exit(1)
    tabs = [t.strip() for t in os.environ.get("BACKFILL_TABS", "").split(",") if t.strip()]
    budget = int(os.environ.get("BACKFILL_MAX_LOOKUPS", "450") or 450)

    info = load_service_account_info(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", ""))
    client = gspread.authorize(Credentials.from_service_account_info(info, scopes=SCOPES))
    sid = os.environ.get("GOOGLE_SPREADSHEET_ID", "").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]{20,})", sid)
    ss = client.open_by_key(m.group(1) if m else sid)

    stop_flag = {"stop": False, "status": ""}
    report = []
    for tab in tabs:
        if budget <= 0 or stop_flag["stop"]:
            break
        try:
            ws = ss.worksheet(tab)
        except gspread.WorksheetNotFound:
            report.append(f"{tab}: タブなし")
            continue
        used, complete, info_row = asyncio.run(process_tab(ws, key, budget, stop_flag))
        budget -= used
        if info_row:
            report.append(f"{info_row[0]}: 今回{info_row[1]}件照合・代表番号{info_row[2]}件・残り{info_row[3]}件")
        if complete and info_row and info_row[1] > 0 and not stop_flag["stop"]:
            n = push_to_kizuna(leads_from_tab(ws), tab)
            report.append(f"{tab}: 全行完了 → KIZUNA取込待ちに{n}件追加")
    if stop_flag["stop"]:
        report.append(f"Googleが {stop_flag['status']} を返したため途中で止めました（印を付けていない行は次回やり直し）")
    if not report:
        report.append("対象の行はもうありません（補完は完了しています）")
    notice("BACKFILL", "\n".join(report))


if __name__ == "__main__":
    main()
