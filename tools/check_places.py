#!/usr/bin/env python3
"""
Google Places API (Find Place) が使えるかを単体で確認する診断スクリプト。
スクレイピングをせず、固定の会社名で1回だけ問い合わせて、
status / error_message / 取得できた電話番号 を表示する。
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp

from utils.places import _lookup_place

# 東京で確実にGoogleマップに載っている会社で試す
SAMPLES = [
    ("株式会社ロイヤルホールディングス", "東京都"),
    ("ヤマト運輸株式会社", "東京都"),
    ("綜合警備保障株式会社", "東京都港区"),
]


async def main() -> int:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY が未設定です")
        return 1

    print(f"APIキー: 先頭6文字 = {api_key[:6]}... 長さ = {len(api_key)}")
    print("-" * 50)

    async with aiohttp.ClientSession() as session:
        for name, addr in SAMPLES:
            phone, full_addr, status, err = await _lookup_place(session, name, addr, api_key)
            print(f"会社: {name}")
            print(f"  status        : {status}")
            print(f"  error_message : {err}")
            print(f"  電話番号       : {phone or '(なし)'}")
            print(f"  住所          : {full_addr or '(なし)'}")
            print("-" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
