#!/usr/bin/env python3
"""サービスアカウントのメールアドレスを表示する。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.credentials import load_service_account_info

creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
info = load_service_account_info(creds_json)
email = info.get("client_email", "取得できませんでした")

print("\n" + "=" * 60)
print("サービスアカウントのメールアドレス:")
print(f"  {email}")
print("=" * 60)
print("\n「法人番号　リスト」スプレッドシートを開き、")
print("右上の「共有」からこのメールアドレスを「編集者」で追加してください。\n")
