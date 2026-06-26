#!/usr/bin/env python3
"""
「法人番号　リスト」スプレッドシートを参照して法人番号を補填する。

動作:
  1. NTAリストスプレッドシートから 会社名→法人番号 の辞書を構築
  2. テレアポリストの各タブを処理し、法人番号が空の行を補填

使い方:
  GOOGLE_SERVICE_ACCOUNT_JSON=... GOOGLE_SPREADSHEET_ID=... python tools/backfill_from_nta_list.py
  TAB_NAME=2026-W24 ... python tools/backfill_from_nta_list.py  # 特定タブのみ
"""
import logging
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from google.oauth2.service_account import Credentials

from utils.credentials import load_service_account_info

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 「法人番号　リスト」スプレッドシートID（固定）
NTA_LIST_ID = "1CrOizzpwy67tXuPy31imRugI0HD3EUtbx_-ocDe8As4"

# テレアポリストの列インデックス（0始まり）
COL_COMPANY = 0   # A列: 会社名
COL_CORP_NUM = 1  # B列: 法人番号
COL_ADDRESS = 2   # C列: 住所

# NTAリストの列インデックス（0始まり）
NTA_COL_NAME = 1   # 法人名
NTA_COL_PREF = 3   # 都道府県
NTA_COL_CITY = 4   # 市区町村
NTA_COL_NUM = 7    # 法人番号


def normalize(name: str) -> str:
    """全角→半角、空白除去、小文字化で会社名を正規化。"""
    name = unicodedata.normalize("NFKC", name)
    name = "".join(name.split())
    return name.lower()


def build_lookup(nta_ss: gspread.Spreadsheet) -> dict:
    """NTAリストの全シートから 正規化会社名→法人番号 の辞書を構築。"""
    lookup = {}
    worksheets = nta_ss.worksheets()
    logger.info(f"NTAリストのシート数: {len(worksheets)}")

    for ws in worksheets:
        logger.info(f"  シート '{ws.title}' を読み込み中...")
        rows = ws.get_all_values()
        if not rows:
            continue
        # ヘッダー行を探す（「法人名」を含む行）
        start = 0
        for idx, row in enumerate(rows[:5]):
            if any("法人名" in cell for cell in row):
                start = idx + 1
                break

        count = 0
        for row in rows[start:]:
            if len(row) > NTA_COL_NUM:
                name = row[NTA_COL_NAME].strip()
                corp_num = row[NTA_COL_NUM].strip()
                if name and corp_num:
                    lookup[normalize(name)] = corp_num
                    count += 1

        logger.info(f"    → {count}件 (累計 {len(lookup)}件)")

    return lookup


def fill_tab(ws: gspread.Worksheet, lookup: dict) -> tuple[int, int]:
    """タブ内の法人番号空白行をlookupで補填。(found, missing) を返す。"""
    header = ws.row_values(1)
    if len(header) < 2 or header[1] != "法人番号":
        logger.warning(f"タブ '{ws.title}': B列が「法人番号」でないためスキップ")
        return 0, 0

    all_values = ws.get_all_values()
    if len(all_values) <= 1:
        logger.info(f"タブ '{ws.title}': データなし")
        return 0, 0

    cell_updates = []
    found = 0
    missing = 0

    for i, row in enumerate(all_values[1:], start=2):
        corp_num = row[COL_CORP_NUM] if len(row) > COL_CORP_NUM else ""
        if corp_num.strip():
            continue  # 既に入力済み

        company = row[COL_COMPANY] if len(row) > COL_COMPANY else ""
        if not company.strip():
            continue

        matched = lookup.get(normalize(company), "")
        if matched:
            cell_updates.append(gspread.Cell(i, COL_CORP_NUM + 1, matched))
            found += 1
        else:
            missing += 1
            logger.debug(f"未一致: {company}")

    if cell_updates:
        ws.update_cells(cell_updates, value_input_option="USER_ENTERED")

    logger.info(f"タブ '{ws.title}': {found}件 補填 / {missing}件 未一致")
    return found, missing


def main():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    info = load_service_account_info(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)

    sa_email = info.get("client_email", "不明")
    logger.info(f"サービスアカウント: {sa_email}")

    # 法人番号リスト読み込み
    logger.info(f"法人番号リスト ({NTA_LIST_ID}) を読み込み中...")
    try:
        nta_ss = client.open_by_key(NTA_LIST_ID)
    except Exception as e:
        print(
            f"\n❌ 法人番号リストを開けません: {e}\n"
            f"\n次の手順でスプレッドシートをサービスアカウントと共有してください:\n"
            f"  1. 「法人番号　リスト」を Google スプレッドシートで開く\n"
            f"  2. 右上「共有」をクリック\n"
            f"  3. 以下のメールアドレスを「編集者」として追加:\n"
            f"     {sa_email}\n",
            file=sys.stderr,
        )
        sys.exit(1)

    lookup = build_lookup(nta_ss)
    logger.info(f"辞書構築完了: {len(lookup):,}件")

    # テレアポリスト更新
    raw_id = os.environ.get("GOOGLE_SPREADSHEET_ID", "").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]{20,})", raw_id)
    sid = m.group(1) if m else raw_id
    leads_ss = client.open_by_key(sid)

    tab_name = os.environ.get("TAB_NAME", "all").strip()
    if tab_name.lower() == "all":
        worksheets = leads_ss.worksheets()
    else:
        worksheets = [leads_ss.worksheet(tab_name)]

    total_found = 0
    total_missing = 0
    for ws in worksheets:
        f, m_count = fill_tab(ws, lookup)
        total_found += f
        total_missing += m_count
        print(f"  ✅ '{ws.title}': {f}件 追加")

    print(f"\n✅ 完了: 法人番号 合計 {total_found}件 追加 / {total_missing}件 未一致")


if __name__ == "__main__":
    main()
