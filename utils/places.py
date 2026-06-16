"""
Google Places API を使って会社名＋住所から電話番号・詳細住所を補完する。
GOOGLE_MAPS_API_KEY 環境変数が未設定の場合はすべてスキップ。

Find Place (legacy) を使用。応答の status / error_message をログに出して
拒否理由(請求未設定・キー制限など)を特定できるようにしている。
"""
import asyncio
import logging
import os
import re
from collections import Counter

import aiohttp

logger = logging.getLogger(__name__)

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
TOKYO_BIAS = "circle:30000@35.6762,139.6503"


async def _lookup_place(
    session: aiohttp.ClientSession, company_name: str, address: str, api_key: str
) -> tuple[str, str, str, str]:
    """(phone, full_address, status, error_message) を返す。"""
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
                return "", "", f"HTTP_{resp.status}", ""
            data = await resp.json()
        status = data.get("status", "UNKNOWN")
        error_message = data.get("error_message", "")
        candidates = data.get("candidates", [])
        if not candidates:
            return "", "", status, error_message
        best = candidates[0]
        phone = best.get("formatted_phone_number", "")
        addr = best.get("formatted_address", "").removeprefix("日本、").strip()
        return phone, addr, status, error_message
    except Exception as e:
        return "", "", "EXCEPTION", str(e)


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
    status_counter: Counter = Counter()
    first_error: dict = {}
    sem = asyncio.Semaphore(concurrency)

    async def _enrich_one(session: aiohttp.ClientSession, lead) -> None:
        nonlocal found_count
        async with sem:
            await asyncio.sleep(0.15)
            phone, addr, status, error_message = await _lookup_place(
                session, lead.company_name, lead.address, api_key
            )
            status_counter[status] += 1
            if status not in ("OK", "ZERO_RESULTS") and "error" not in first_error:
                first_error["status"] = status
                first_error["message"] = error_message
            if phone:
                lead.phone = phone
                found_count += 1
            # 番地がない住所（数字を含まない）だけ上書き
            if addr and not re.search(r"\d", lead.address):
                lead.address = addr

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_enrich_one(session, l) for l in targets])

    # 応答ステータスの内訳をログ出力（原因特定用）
    logger.info(f"[Places] 応答ステータス内訳: {dict(status_counter)}")
    if first_error:
        logger.warning(
            f"[Places] 拒否理由: status={first_error.get('status')} "
            f"message={first_error.get('message')}"
        )

    logger.info(f"[Places] Googleマップ補完完了: {len(targets)}件中 電話番号 {found_count}件")
    return found_count
