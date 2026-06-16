#!/usr/bin/env python3
"""
既存スプレッドシートの電話番号を後から補填する。
TAB_NAME で指定したタブの「電話番号」列が空の行を
Google Places API で補完してスプレッドシートに書き戻す。
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

COL_COMPANY = 0
COL_ADDRESS = 1
COL_PHONE = 2

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
TOKYO_BIAS = "circle:30000@35.6762,139.6503"


async def _find_place_id(session, company_name, address, api_key):
    params = {
        "input": f"{company_name} {address}",
        "inputtype": "textquery",
        "fields": "place_id",
        "key": api_key,
        "language": "ja",
        "locationbias": TOKYO_BIAS,
    }
    async with session.get(FIND_PLACE_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        data = await resp.json()
    candidates = data.get("candidates", [])
    return candidates[0].get("place_id", "") if candidates else ""


async def _get_phone(session, place_id, api_key):
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,formatted_address",
        "key": api_key,
        "language": "ja",
    }
    async with session.get(DETAILS_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
        data = await resp.json()
    result = data.get("result", {})
    return (
        result.get("formatted_phone_number", ""),
        result.get("formatted_address", "").removeprefix("日本、").strip(),
    )


async def lookup(session, company_name, address, api_key):
    try:
        place_id = await _find_place_id(session, company_name, address, api_key)
        if not place_id:
            return "", ""
        return await _get_phone(session, place_id, api_key)
    except Exception as e:
        logger.debug(f"エラー ({company_name}): {e}")
        return "", ""


async def backfill(ws: gspread.Worksheet, api_key: str, concurrency: int = 5) -> int:
    all_values = ws.get_all_values()
    if not all_values:
        logger.info("シートが空です")
        return 0

    data_rows = all_values[1:]
    targets = []
    for i, row in enumerate(data_rows):
        phone_val = row[COL_PHONE] if len(row) > COL_PHONE else ""
        if not phone_val.strip():
            company = row[COL_COMPANY] if len(row) > COL_COMPANY else ""
            address = row[COL_ADDRESS] if len(row) > COL_ADDRESS else ""
            if company:
                targets.append((i + 2, company, address))

    logger.info(f"電話番号が空の行: {len(targets)}件 / 全{len(data_rows)}件")
    if not targets:
        return 0

    sem = asyncio.Semaphore(concurrency)
    results = {}

    async def _do(session, sheet_row, company, address):
        async with sem:
            await asyncio.sleep(0.15)
            phone, full_addr = await lookup(session, company, address, api_key)
            results[sheet_row] = (phone, full_addr, company, address)

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_do(session, r, c, a) for r, c, a in targets])

    found = 0
    cell_updates = []
    for sheet_row, (phone, full_addr, company, address) in results.items():
        if phone:
            cell_updates.append(gspread.Cell(sheet_row, COL_PHONE + 1, phone))
            found += 1
        if full_addr and not re.search(r"\d", address):
            cell_updates.append(gspread.Cell(sheet_row, COL_ADDRESS + 1, full_addr))

    if cell_updates:
        ws.update_cells(cell_updates, value_input_option="USER_ENTERED")
        logger.info(f"スプレッドシートを更新しました ({len(cell_updates)}セル)")

    logger.info(f"補填完了: {len(targets)}件中 電話番号 {found}件")
    return found


def main():
    tab_name = os.environ.get("TAB_NAME", "2026-W23")
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY が未設定です", file=sys.stderr)
        sys.exit(1)

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

    found = asyncio.run(backfill(ws, api_key))
    print(f"\n✅ 補填完了: 電話番号 {found}件 追加しました")


if __name__ == "__main__":
    main()
