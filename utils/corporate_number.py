"""
国税庁法人番号公表システムAPI を使って会社名から法人番号を補完する。
NTA_API_KEY 環境変数（アプリケーションID）が未設定の場合はスキップ。

APIの利用登録（無料）: https://www.houjin-bangou.nta.go.jp/apiriyou/
"""
import asyncio
import logging
import os

import aiohttp

logger = logging.getLogger(__name__)

NTA_URL = "https://api.houjin-bangou.nta.go.jp/4/name"


async def _lookup_one(
    session: aiohttp.ClientSession, company_name: str, address: str, app_id: str
) -> tuple[str, str]:
    """(corporate_number, legal_name) を返す。未取得は空文字。"""
    params = {
        "appId": app_id,
        "name": company_name,
        "type": "02",   # 前方一致検索
        "output": "json",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(NTA_URL, params=params, timeout=timeout) as resp:
            if resp.status != 200:
                return "", ""
            data = await resp.json(content_type=None)
        corps = data.get("corporation", [])
        if not corps:
            return "", ""
        addr_prefix = address[:4] if len(address) >= 4 else address
        for corp in corps:
            corp_addr = (
                corp.get("prefectureName", "")
                + corp.get("cityName", "")
                + corp.get("streetNumber", "")
            )
            if addr_prefix and addr_prefix in corp_addr:
                return corp.get("corporateNumber", ""), corp.get("name", "")
        return corps[0].get("corporateNumber", ""), corps[0].get("name", "")
    except Exception as e:
        logger.debug(f"法人番号取得エラー ({company_name}): {e}")
        return "", ""


async def enrich_with_corporate_numbers(leads: list, concurrency: int = 5) -> int:
    """
    corporate_number が空のリードに対して法人番号と法人名を補完する。
    補完できた件数を返す。
    """
    app_id = os.environ.get("NTA_API_KEY", "")
    if not app_id:
        logger.info("[法人番号] NTA_API_KEY が未設定のためスキップ")
        return 0

    targets = [l for l in leads if not l.corporate_number]
    if not targets:
        return 0

    logger.info(f"[法人番号] 国税庁API検索開始: {len(targets)}件")
    found = 0
    sem = asyncio.Semaphore(concurrency)

    async def _do(session: aiohttp.ClientSession, lead) -> None:
        nonlocal found
        async with sem:
            await asyncio.sleep(0.1)
            num, legal = await _lookup_one(session, lead.company_name, lead.address, app_id)
            if num:
                lead.corporate_number = num
                if legal:
                    lead.legal_name = legal
                found += 1

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_do(session, l) for l in targets])

    logger.info(f"[法人番号] 完了: {len(targets)}件中 {found}件 取得")
    return found
