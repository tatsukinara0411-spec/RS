#!/usr/bin/env python3
"""
屋号から法人名・法人番号を補填する（新フォーマット対応）。

動作:
  1. テレアポリストの各タブを処理
  2. 法人名・法人番号が両方空の行を対象に、国税庁APIで屋号を検索
  3. 法人名（B列）と法人番号（C列）を補填

事前準備:
  - GitHub Secrets に NTA_API_KEY を登録（申請: https://www.houjin-bangou.nta.go.jp/apiriyou/）

使い方:
  TAB_NAME=all ... python tools/backfill_legal_name.py
  TAB_NAME=2026-W27 ... python tools/backfill_legal_name.py
"""
import asyncio
import logging
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from google.oauth2.service_account import Credentials

from utils.credentials import load_service_account_info
from utils.corporate_number import enrich_with_corporate_numbers

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class _Row:
    """スプレッドシートの1行をLeadと同じインターフェースで扱う"""
    def __init__(self, company_name: str, address: str):
        self.company_name = company_name
        self.address = address
        self.corporate_number = ""
        self.legal_name = ""


async def fill_tab(ws: gspread.Worksheet) -> tuple:
    """タブの法人名・法人番号を補填。(found, missing) を返す。"""
    header = ws.row_values(1)
    if not header:
        return 0, 0

    if len(header) >= 3 and header[2] == "法人番号":
        col_company = 0   # A: 屋号
        col_legal = 1     # B: 法人名
        col_corp_num = 2  # C: 法人番号
        col_address = 3   # D: 住所
    else:
        logger.info(f"タブ '{ws.title}': 新フォーマットではないためスキップ")
        return 0, 0

    all_values = ws.get_all_values()
    if len(all_values) <= 1:
        return 0, 0

    targets = []
    for i, row in enumerate(all_values[1:], start=2):
        corp_num = row[col_corp_num] if len(row) > col_corp_num else ""
        legal = row[col_legal] if len(row) > col_legal else ""
        if corp_num.strip() or legal.strip():
            continue  # どちらかが入力済みならスキップ
        company = row[col_company] if len(row) > col_company else ""
        if not company.strip():
            continue
        address = row[col_address] if len(row) > col_address else ""
        targets.append((i, company.strip(), address.strip()))

    if not targets:
        logger.info(f"タブ '{ws.title}': 補填対象なし")
        return 0, 0

    logger.info(f"タブ '{ws.title}': {len(targets)}件を国税庁APIで検索中...")
    rows = [_Row(company, address) for _, company, address in targets]
    await enrich_with_corporate_numbers(rows, concurrency=3)

    cell_updates = []
    found = 0
    missing = 0
    for (sheet_row, company, _), row in zip(targets, rows):
        if row.corporate_number:
            cell_updates.append(gspread.Cell(sheet_row, col_corp_num + 1, row.corporate_number))
            if row.legal_name:
                cell_updates.append(gspread.Cell(sheet_row, col_legal + 1, row.legal_name))
            found += 1
        else:
            missing += 1
            logger.debug(f"未一致: {company}")

    if cell_updates:
        ws.update_cells(cell_updates, value_input_option="USER_ENTERED")

    logger.info(f"タブ '{ws.title}': {found}件 補填 / {missing}件 未一致")
    return found, missing


def main():
    app_id = os.environ.get("NTA_API_KEY", "").strip()
    if not app_id:
        print(
            "\n❌ NTA_API_KEY が未設定です。\n"
            "\n申請（無料）が必要です:\n"
            "  https://www.houjin-bangou.nta.go.jp/apiriyou/\n"
            "\n申請後、GitHub Secrets に NTA_API_KEY を登録してください。\n",
            file=sys.stderr,
        )
        sys.exit(1)

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    info = load_service_account_info(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    client = gspread.authorize(creds)

    raw_id = os.environ.get("GOOGLE_SPREADSHEET_ID", "").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]{20,})", raw_id)
    sid = m.group(1) if m else raw_id
    ss = client.open_by_key(sid)

    tab_name = os.environ.get("TAB_NAME", "all").strip()
    if tab_name.lower() == "all":
        worksheets = ss.worksheets()
    else:
        worksheets = [ss.worksheet(tab_name)]

    total_found = 0
    total_missing = 0
    for ws in worksheets:
        f, m_count = asyncio.run(fill_tab(ws))
        total_found += f
        total_missing += m_count
        if f > 0:
            print(f"  ✅ '{ws.title}': {f}件 追加")

    print(f"\n✅ 完了: 法人名 合計 {total_found}件 補填 / {total_missing}件 未一致")


if __name__ == "__main__":
    main()
