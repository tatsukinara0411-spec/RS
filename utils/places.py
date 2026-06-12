"""
Google Places API を使って会社名＋住所から電話番号・詳細住所を補完する。
GOOGLE_MAPS_API_KEY 環境変数が未設定の場合はすべてスキップ。
"""
import asyncio
import logging
import os

import aiohttp

logger = logging.getLogger(__name__)

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
TOKYO_BIAS = "circle:30000@35.6762,139.6503"


async def _lookup_place(
    session: aiohttp.ClientSession, company_name: str, address: str, api_key: str
) -> tuple[str, str]:
    """(phone, full_address) を返す。見つからなければ ("", "") を返す。"""
    params = {
        "input": f"{company_name} {address}",
        "inputtype": "textquery",
        "fields": "formatted_phone_number,formatted_address,name",
        "key": api_key,
        "language": "ja",
        "locationbias": TOKYO_BIAS,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(FIND_PLACE_URL, params=params, timeout=timeout) as resp:
            if resp.status != 200:
                return "", ""
            data = await resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return "", ""
        best = candidates[0]
        phone = best.get("formatted_phone_number", "")
        addr = best.get("formatted_address", "").removeprefix("日本、").strip()
        return phone, addr
    except Exception as e:
        logger.debug(f"[Places] エラー ({company_name}): {e}")
        return "", ""


async def enrich_with_places(leads: list, concurrency: int = 5) -> int:
    """
    phone が空のリードに対してGoogleマップAPIで電話番号・住所を補完する。
    補完できた件数を返す。
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.info("[Places] GOOGLE_MAPS_API_KEY が未設定のためスキップ")
        return 0

    targets = [l for l in leads if not l.phone]
    if not targets:
        logger.info("[Places] 電話番号補完対象なし（全件取得済み）")
        return 0

    logger.info(f"[Places] Googleマップ補完開始: {len(targets)}件")

    found_count = 0
    sem = asyncio.Semaphore(concurrency)

    async def _enrich_one(session: aiohttp.ClientSession, lead) -> None:
        nonlocal found_count
        async with sem:
            await asyncio.sleep(0.15)
            phone, addr = await _lookup_place(session, lead.company_name, lead.address, api_key)
            if phone:
                lead.phone = phone
                found_count += 1
            # 番地がない住所（数字を含まない）だけ上書き
            import re
            if addr and not re.search(r"\d", lead.address):
                lead.address = addr

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_enrich_one(session, l) for l in targets])

    logger.info(f"[Places] Googleマップ補完完了: {len(targets)}件中 電話番号 {found_count}件")
    return found_count
