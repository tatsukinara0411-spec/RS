"""
Google Places API を使って会社名から「会社の代表電話番号・住所」を補完する。
GOOGLE_MAPS_API_KEY 環境変数が未設定の場合はすべてスキップ。

電話番号は Find Place 単体では取れないため2段階で取得する:
  1. Find Place From Text → place_id を取得
  2. Place Details → formatted_phone_number / formatted_address を取得

予算ガード:
  PLACES_MAX_LOOKUPS       1回の実行で調べる上限（既定 1500件）
  PLACES_MONTHLY_BUDGET    1か月で調べる上限（既定 5000件）
  いずれも超えると以降はスキップし、実行結果ページに警告を出す。

精度ガード:
  Googleマップが返した施設名が会社名と一致しない場合は採用しない
  （別の店舗・別会社の番号を入れてしまうのを防ぐ）。
"""
import asyncio
import logging
import os
import re
import unicodedata
from collections import Counter

import aiohttp

from utils.api_budget import (
    COST_PER_LOOKUP_JPY,
    add_month_lookups,
    budget_status,
    notify,
)

logger = logging.getLogger(__name__)

FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
TOKYO_BIAS = "circle:30000@35.6762,139.6503"

CORP_SUFFIXES = [
    "株式会社", "有限会社", "合同会社", "合資会社", "合名会社",
    "一般社団法人", "一般財団法人", "公益社団法人", "公益財団法人",
    "医療法人社団", "医療法人財団", "医療法人", "社会福祉法人", "学校法人",
    "宗教法人", "特定非営利活動法人", "独立行政法人", "国立大学法人",
]


def _env_int(name: str, default: int) -> int:
    """未設定・空文字・不正値でも落ちないように整数を読む。"""
    raw = (os.environ.get(name) or "").strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _norm(s: str) -> str:
    return "".join(unicodedata.normalize("NFKC", s or "").split()).lower()


def _core_name(name: str) -> str:
    """法人格・記号を除いた中心部分を取り出す（照合用）。"""
    s = unicodedata.normalize("NFKC", name or "")
    s = re.sub(r"[（(【\[＜<「『][^）)】\]＞>」』]*[）)】\]＞>」』]", " ", s)
    for mk in ["※", "/", "／", "\\", "｜", "|"]:
        s = s.split(mk)[0]
    for kw in CORP_SUFFIXES:
        s = s.replace(kw, " ")
    s = re.sub(r"[・\-－―—\s]+", "", s)
    return s.strip().lower()


def _is_match(company_name: str, place_name: str) -> bool:
    """Googleが返した施設名が、その会社のものと見なせるか。"""
    if not place_name:
        return False
    a, b = _norm(company_name), _norm(place_name)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    ca, cb = _core_name(company_name), _core_name(place_name)
    if len(ca) >= 3 and len(cb) >= 3 and (ca in cb or cb in ca):
        return True
    return False


async def _find_place(
    session: aiohttp.ClientSession, company_name: str, address: str, api_key: str
) -> tuple[str, str, str, str]:
    """(place_id, place_name, status, error_message) を返す。"""
    params = {
        "input": f"{company_name} {address}",
        "inputtype": "textquery",
        "fields": "place_id,name",
        "key": api_key,
        "language": "ja",
        "locationbias": TOKYO_BIAS,
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(FIND_PLACE_URL, params=params, timeout=timeout) as resp:
        if resp.status != 200:
            return "", "", f"HTTP_{resp.status}", ""
        data = await resp.json()
    status = data.get("status", "UNKNOWN")
    candidates = data.get("candidates", [])
    if not candidates:
        return "", "", status, data.get("error_message", "")
    return (
        candidates[0].get("place_id", ""),
        candidates[0].get("name", ""),
        status,
        data.get("error_message", ""),
    )


async def _place_details(
    session: aiohttp.ClientSession, place_id: str, api_key: str
) -> tuple[str, str, str, str]:
    """(phone, address, status, error_message) を返す。"""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,formatted_address",
        "key": api_key,
        "language": "ja",
    }
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(DETAILS_URL, params=params, timeout=timeout) as resp:
        if resp.status != 200:
            return "", "", f"HTTP_{resp.status}", ""
        data = await resp.json()
    result = data.get("result", {})
    addr = result.get("formatted_address", "").removeprefix("日本、").strip()
    return (
        result.get("formatted_phone_number", ""),
        addr,
        data.get("status", "UNKNOWN"),
        data.get("error_message", ""),
    )


async def enrich_with_places(leads: list, concurrency: int = 5) -> int:
    """
    phone が空のリードに対してGoogleマップで代表電話番号・住所を補完する。
    補完できた件数を返す。
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.info("[Places] GOOGLE_MAPS_API_KEY が未設定のためスキップ")
        return 0

    max_per_run = _env_int("PLACES_MAX_LOOKUPS", 1500)
    monthly_budget = _env_int("PLACES_MONTHLY_BUDGET", 5000)

    used, remaining, pct = budget_status(monthly_budget)
    if remaining <= 0:
        notify(
            f"🛑 **Googleマップ 月次上限に到達したため補完をスキップしました**\n\n"
            f"- 今月の利用: {used:,}件 / 上限 {monthly_budget:,}件\n"
            f"- 電話番号・住所は空欄のままになります。\n"
            f"- 続ける場合はシークレット `PLACES_MONTHLY_BUDGET` の値を引き上げてください。"
        )
        return 0

    # 番号が全く無いものを先に、求人ページの番号しか無いものを後に調べる
    targets = [l for l in leads if not l.phone]
    targets.sort(key=lambda l: bool(getattr(l, "listing_phone", "")))
    if not targets:
        logger.info("[Places] 電話番号補完対象なし（全件取得済み）")
        return 0

    limit = min(len(targets), max_per_run, remaining)
    skipped = len(targets) - limit
    targets = targets[:limit]

    logger.info(
        f"[Places] 補完開始: {len(targets)}件 "
        f"(今月利用 {used:,}/{monthly_budget:,}件, 残り {remaining:,}件)"
    )
    if skipped > 0:
        logger.warning(f"[Places] 上限により {skipped}件 をスキップします")

    found_count = 0
    mismatch_count = 0
    calls = 0
    status_counter: Counter = Counter()
    first_error: dict = {}
    sem = asyncio.Semaphore(concurrency)

    async def _enrich_one(session: aiohttp.ClientSession, lead) -> None:
        nonlocal found_count, mismatch_count, calls
        async with sem:
            await asyncio.sleep(0.15)
            try:
                place_id, place_name, status, err = await _find_place(
                    session, lead.company_name, lead.address, api_key
                )
                calls += 1
                status_counter[status] += 1
                if status not in ("OK", "ZERO_RESULTS") and "status" not in first_error:
                    first_error["status"] = status
                    first_error["message"] = err
                if not place_id:
                    return
                # 別会社・別店舗の番号を入れないよう名前を照合
                if not _is_match(lead.company_name, place_name):
                    mismatch_count += 1
                    logger.debug(f"[Places] 不一致のため不採用: {lead.company_name} ≠ {place_name}")
                    return
                phone, addr, dstatus, derr = await _place_details(session, place_id, api_key)
                calls += 1
                status_counter[dstatus] += 1
                if phone:
                    lead.phone = phone
                    lead.phone_source = "google"
                    found_count += 1
                if addr and not re.search(r"\d", lead.address):
                    lead.address = addr
            except Exception as e:
                status_counter["EXCEPTION"] += 1
                logger.debug(f"[Places] エラー ({lead.company_name}): {e}")

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_enrich_one(session, l) for l in targets])

    total_used = add_month_lookups(len(targets))
    cost = total_used * COST_PER_LOOKUP_JPY
    _, remaining_after, pct_after = budget_status(monthly_budget)

    logger.info(f"[Places] 応答ステータス内訳: {dict(status_counter)}")
    logger.info(f"[Places] 名前不一致で不採用: {mismatch_count}件")
    logger.info(
        f"[Places] 完了: {len(targets)}件中 電話番号 {found_count}件 "
        f"(API呼び出し {calls}回 / 今月累計 {total_used:,}件・概算 {cost:,}円)"
    )

    if first_error.get("status") == "REQUEST_DENIED":
        notify(
            "🛑 **Googleマップが拒否されました（REQUEST_DENIED）**\n\n"
            f"理由: {first_error.get('message','')}\n\n"
            "Google Cloud の課金設定・Places APIの有効化を確認してください。\n"
            "https://console.cloud.google.com/billing"
        )
    elif pct_after >= 80:
        notify(
            f"⚠️ **Googleマップの月次予算が残りわずかです**\n\n"
            f"- 今月の利用: {total_used:,}件 / 上限 {monthly_budget:,}件（{pct_after:.0f}%）\n"
            f"- 残り: {remaining_after:,}件\n"
            f"- 概算費用: 約 {cost:,}円\n\n"
            f"上限に達すると電話番号の補完が止まります。"
        )
    else:
        notify(
            f"✅ Googleマップ補完: {found_count:,}件に電話番号を設定 "
            f"(今月 {total_used:,}/{monthly_budget:,}件・概算 {cost:,}円)"
        )

    return found_count
