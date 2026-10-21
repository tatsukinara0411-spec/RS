#!/usr/bin/env python3
"""
Google Places API（GOOGLE_MAPS_API_KEY）が有効か、
実在の会社名から正しい代表電話・住所が取れるかを検証する。
"""
import asyncio
import os

import aiohttp

FIND_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# 実在の会社名（求人サイトで実際に出てきたもの）
SAMPLES = [
    ("テイケイ株式会社", "東京都"),
    ("株式会社全日警", "東京都"),
    ("テイシン警備株式会社", "東京都"),
    ("SPD株式会社", "東京都"),
    ("株式会社リンクスタッフグループ", "東京都品川区"),
    ("株式会社セントラルサービスシステム", "東京都"),
    ("グリーン警備保障株式会社", "東京都"),
    ("株式会社セカンドブリュー", "東京都渋谷区"),
]


async def test_one(session, name, area, key):
    q = f"{name} {area}"
    p1 = {"input": q, "inputtype": "textquery", "fields": "place_id,name,formatted_address",
          "key": key, "language": "ja"}
    async with session.get(FIND_URL, params=p1) as r:
        d1 = await r.json()
    st1 = d1.get("status")
    if st1 != "OK":
        print(f"  [{name}] FindPlace status={st1} err={d1.get('error_message','')}")
        return st1
    cand = d1.get("candidates", [])
    if not cand:
        print(f"  [{name}] 候補なし")
        return "ZERO"
    pid = cand[0].get("place_id")
    matched = cand[0].get("name", "")
    p2 = {"place_id": pid, "fields": "name,formatted_phone_number,formatted_address",
          "key": key, "language": "ja"}
    async with session.get(DETAILS_URL, params=p2) as r:
        d2 = await r.json()
    st2 = d2.get("status")
    res = d2.get("result", {})
    phone = res.get("formatted_phone_number", "(なし)")
    addr = res.get("formatted_address", "").replace("日本、", "")
    print(f"  [{name}]")
    print(f"      → 一致した施設名: {matched}")
    print(f"      → 電話: {phone}")
    print(f"      → 住所: {addr}")
    return st2


async def main():
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not key:
        print("❌ GOOGLE_MAPS_API_KEY が未設定")
        return
    print(f"APIキー: 先頭6文字={key[:6]}... 長さ={len(key)}")
    print("=" * 60)
    statuses = []
    async with aiohttp.ClientSession() as session:
        for name, area in SAMPLES:
            try:
                st = await test_one(session, name, area, key)
                statuses.append(st)
            except Exception as e:
                print(f"  [{name}] 例外: {e}")
            await asyncio.sleep(0.3)
    print("=" * 60)
    print("ステータス集計:", {s: statuses.count(s) for s in set(statuses)})
    if any(s == "REQUEST_DENIED" for s in statuses):
        print("⚠️ REQUEST_DENIED: APIキー無効 or Places API未有効化 or 課金未設定")
    if any(s == "OVER_QUERY_LIMIT" for s in statuses):
        print("⚠️ OVER_QUERY_LIMIT: 無料枠超過 or 課金未設定")


if __name__ == "__main__":
    asyncio.run(main())
