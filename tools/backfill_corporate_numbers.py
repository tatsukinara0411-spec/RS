#!/usr/bin/env python3
"""
既存スプレッドシートタブに法人番号列を追加・補填する。

動作:
  1. 指定タブのB列が「法人番号」でなければ列を挿入してヘッダーを設定
  2. 法人番号が空の行を国税庁法人番号公表システムで検索して補填
  3. NTA_API_KEY が設定されていれば公式API、未設定なら公開HTMLを使用

使い方:
  TAB_NAME=2026-W24 python tools/backfill_corporate_numbers.py
"""
import asyncio
import logging
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import gspread
from google.oauth2.service_account import Credentials

from utils.credentials import load_service_account_info

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 列インデックス（0始まり）
COL_COMPANY = 0       # A列: 会社名
COL_CORP_NUM = 1      # B列: 法人番号（挿入後）
COL_ADDRESS = 2       # C列: 住所（挿入後）

NTA_API_URL = "https://api.houjin-bangou.nta.go.jp/4/name"
NTA_HTML_URL = "https://www.houjin-bangou.nta.go.jp/henkorireki-johoto.html"


# ── 国税庁 公式API（NTA_API_KEY が必要） ──────────────────────────

async def _lookup_via_api(session, company_name, address, app_id):
    """公式APIで会社名→法人番号を検索。(corp_number, source) を返す。"""
    params = {
        "appId": app_id,
        "name": company_name,
        "type": "02",    # 前方一致
        "output": "json",
    }
    try:
        async with session.get(
            NTA_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status != 200:
                return "", "api_error"
            data = await resp.json(content_type=None)
        corps = data.get("corporation", [])
        if not corps:
            return "", "not_found"
        # 住所の都道府県・市区町村が一致する候補を優先
        addr_prefix = address[:4] if len(address) >= 4 else address
        for corp in corps:
            corp_addr = (
                corp.get("prefectureName", "")
                + corp.get("cityName", "")
                + corp.get("streetNumber", "")
            )
            if addr_prefix and addr_prefix in corp_addr:
                return corp.get("corporateNumber", ""), "api_match"
        # 先頭候補をフォールバック
        return corps[0].get("corporateNumber", ""), "api_fallback"
    except Exception as e:
        logger.debug(f"API検索エラー ({company_name}): {e}")
        return "", "api_exception"


# ── 国税庁 公開HTML検索（APIキー不要） ────────────────────────────

async def _lookup_via_html(session, company_name):
    """公開検索ページから会社名で法人番号を検索。"""
    params = {
        "selHouzinNo": "",
        "IFD_OFN_flg": "2",
        "SZT_flg": "1",
        "textHouzinMei": company_name,
        "kenCode": "13",    # 東京都（13）に限定して精度向上
    }
    try:
        async with session.get(
            "https://www.houjin-bangou.nta.go.jp/henkorireki-johoto.html",
            params=params,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"Accept-Language": "ja,en;q=0.9"},
        ) as resp:
            if resp.status != 200:
                return ""
            html = await resp.text()
        # 13桁の法人番号をHTMLから抽出（最初の候補）
        matches = re.findall(r'\b([0-9]{13})\b', html)
        return matches[0] if matches else ""
    except Exception as e:
        logger.debug(f"HTML検索エラー ({company_name}): {e}")
        return ""


# ── 統合ルックアップ ──────────────────────────────────────────────

async def lookup(session, company_name, address, app_id):
    """法人番号を返す。取得できなければ空文字。"""
    if app_id:
        corp_num, _ = await _lookup_via_api(session, company_name, address, app_id)
        if corp_num:
            return corp_num
    # APIキーなし or API失敗 → HTMLフォールバック
    return await _lookup_via_html(session, company_name)


# ── スプレッドシート操作 ──────────────────────────────────────────

def _ensure_corp_num_column(ws: gspread.Worksheet) -> bool:
    """
    B列が「法人番号」でなければ列を挿入してヘッダーをセット。
    True=挿入した / False=既に存在
    """
    header = ws.row_values(1)
    if len(header) >= 2 and header[1] == "法人番号":
        logger.info("法人番号列は既に存在します（スキップ）")
        return False

    logger.info("B列に「法人番号」列を挿入します")
    # B列（index=2、1始まり）に空列を挿入
    ws.spreadsheet.batch_update({
        "requests": [{
            "insertDimension": {
                "range": {
                    "sheetId": ws.id,
                    "dimension": "COLUMNS",
                    "startIndex": 1,   # 0始まり → B列
                    "endIndex": 2,
                },
                "inheritFromBefore": False,
            }
        }]
    })
    # ヘッダーに「法人番号」をセット
    ws.update_cell(1, 2, "法人番号")
    logger.info("法人番号列の挿入完了")
    return True


async def backfill(ws: gspread.Worksheet, app_id: str, concurrency: int = 3) -> int:
    _ensure_corp_num_column(ws)

    all_values = ws.get_all_values()
    if len(all_values) <= 1:
        logger.info("データ行がありません")
        return 0

    data_rows = all_values[1:]
    targets = []
    for i, row in enumerate(data_rows):
        corp_num = row[COL_CORP_NUM] if len(row) > COL_CORP_NUM else ""
        if not corp_num.strip():
            company = row[COL_COMPANY] if len(row) > COL_COMPANY else ""
            address = row[COL_ADDRESS] if len(row) > COL_ADDRESS else ""
            if company:
                targets.append((i + 2, company, address))  # i+2 = スプレッドシート行番号

    logger.info(f"法人番号が空の行: {len(targets)}件 / 全{len(data_rows)}件")
    if not targets:
        return 0

    sem = asyncio.Semaphore(concurrency)
    results = {}

    async def _do(session, sheet_row, company, address):
        async with sem:
            await asyncio.sleep(0.3)
            num = await lookup(session, company, address, app_id)
            results[sheet_row] = (num, company)

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_do(session, r, c, a) for r, c, a in targets])

    found = 0
    cell_updates = []
    for sheet_row, (num, company) in results.items():
        if num:
            cell_updates.append(gspread.Cell(sheet_row, COL_CORP_NUM + 1, num))
            found += 1
        else:
            logger.debug(f"未取得: {company}")

    if cell_updates:
        ws.update_cells(cell_updates, value_input_option="USER_ENTERED")
        logger.info(f"スプレッドシートを更新しました ({len(cell_updates)}セル)")

    logger.info(f"補填完了: {len(targets)}件中 法人番号 {found}件")
    return found


def main():
    tab_name = os.environ.get("TAB_NAME", "2026-W24")
    app_id = os.environ.get("NTA_API_KEY", "")  # 未設定でもHTMLフォールバックで動く

    if app_id:
        logger.info("モード: 国税庁公式API")
    else:
        logger.info("モード: 公開HTMLフォールバック（NTA_API_KEY 未設定）")

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    info = load_service_account_info(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID", "").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]{20,})", spreadsheet_id)
    sid = m.group(1) if m else spreadsheet_id

    ss = client.open_by_key(sid)
    ws = ss.worksheet(tab_name)
    logger.info(f"タブ '{tab_name}' を開きました")

    found = asyncio.run(backfill(ws, app_id))
    print(f"\n✅ 補填完了: 法人番号 {found}件 追加しました")


if __name__ == "__main__":
    main()
