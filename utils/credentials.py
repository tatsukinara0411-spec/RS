"""Googleサービスアカウント認証情報の検証(標準ライブラリのみ使用)

GitHub Actionsのシークレット GOOGLE_SERVICE_ACCOUNT_JSON が壊れている場合に、
スクレイピング(約10分)を実行する前に数秒で失敗させ、
原因と対処法を日本語で表示する。シークレットの中身自体は絶対にログに出さない。
"""
import json
import os
import re
import sys

REQUIRED_KEYS = ["type", "project_id", "private_key_id", "private_key", "client_email"]

REGISTER_GUIDE = """\
【正しい登録手順】
  1. Google Cloud Console → IAMと管理 → サービスアカウント → キー → 鍵を追加(JSON)
     でダウンロードした .json ファイルをテキストエディタで開く
  2. Ctrl+A → Ctrl+C で「ファイル全文」をコピー(一部だけ・例文はNG)
  3. GitHub → リポジトリ → Settings → Secrets and variables → Actions
     → GOOGLE_SERVICE_ACCOUNT_JSON → Update
  4. 入力欄を全消去してから貼り付け → Update secret"""


class CredentialsError(Exception):
    """サービスアカウントJSONの不備。メッセージに原因と対処法を含む。"""


def _diagnose_parse_error(raw: str, err: json.JSONDecodeError) -> str:
    causes = []
    if re.search(r"^\s*\.\.\.", raw, re.M) or '"xxx"' in raw or "xxx@xxx" in raw:
        causes.append(
            "「...」や「xxx」が含まれています。サンプル(例)のJSONが貼り付けられています。"
            "Google Cloudからダウンロードした実際のファイルの中身を貼ってください。"
        )
    if not raw.lstrip().startswith("{"):
        causes.append("先頭が「{」で始まっていません。余計な文字が混ざっています。")
    if not raw.rstrip().endswith("}"):
        causes.append("末尾が「}」で終わっていません。コピーが途中で切れています。")
    if '"private_key"' in raw and "-----BEGIN" not in raw:
        causes.append("private_key に鍵本体(-----BEGIN ...)が含まれていません。")
    if not causes:
        causes.append("JSONの一部だけがコピーされた、または貼り付け時に内容が変化した可能性があります。")

    lines = raw.count("\n") + 1
    return (
        f"GOOGLE_SERVICE_ACCOUNT_JSON がJSONとして読み取れません。\n"
        f"  エラー位置: {err.lineno}行目 {err.colno}文字目 (全体: {lines}行 {len(raw)}文字)\n"
        f"  ※ 正しいサービスアカウントJSONは private_key だけで約1,700文字あります。\n"
        + "".join(f"  考えられる原因: {c}\n" for c in causes)
        + REGISTER_GUIDE
    )


def load_service_account_info(raw: str) -> dict:
    """JSON文字列を検証して辞書を返す。不備があれば CredentialsError を送出。"""
    raw = raw.strip().lstrip("﻿")
    if not raw:
        raise CredentialsError(
            "GOOGLE_SERVICE_ACCOUNT_JSON が空です。\n" + REGISTER_GUIDE
        )

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as err:
        raise CredentialsError(_diagnose_parse_error(raw, err)) from err

    missing = [k for k in REQUIRED_KEYS if not info.get(k)]
    if missing:
        raise CredentialsError(
            f"JSONは読み取れましたが、必須キーが不足しています: {', '.join(missing)}\n"
            "ダウンロードしたファイル全文を貼り直してください。\n" + REGISTER_GUIDE
        )
    if "-----BEGIN" not in info["private_key"]:
        raise CredentialsError(
            "private_key の形式が不正です(-----BEGIN ... が見つかりません)。\n"
            + REGISTER_GUIDE
        )
    return info


def validate() -> None:
    """CI用の事前チェック。成功時は接続情報の概要を表示、失敗時はexit 1。"""
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    try:
        info = load_service_account_info(raw)
    except CredentialsError as err:
        print(f"\n❌ シークレット検証エラー\n\n{err}\n", file=sys.stderr)
        sys.exit(1)

    print("✅ GOOGLE_SERVICE_ACCOUNT_JSON は正常です")
    print(f"   project_id  : {info['project_id']}")
    print(f"   client_email: {info['client_email']}")
    if os.environ.get("GOOGLE_SPREADSHEET_ID"):
        print(
            "   ※ GOOGLE_SPREADSHEET_ID が設定されています。対象スプレッドシートを"
            f"上記 client_email に「編集者」として共有しておいてください。"
        )


if __name__ == "__main__":
    validate()
