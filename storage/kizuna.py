"""
収集結果を KIZUNA CRM の「取込待ち」（Supabase の scrape_staging）へ送る。

KIZUNA 側の関数 scrape_stage_push(p_token, p_batch, p_rows) を呼ぶ。この関数は合言葉（トークン）が
一致したときだけ取込待ちの表に行を追加する（テレマのリストなど他の表には触れない）。
取込待ちからテレマの架電リストへの取込は、KIZUNA の「架電リスト取込」画面で人がボタンを押して行う。

必要な設定（GitHub の Secrets）:
  KIZUNA_INGEST_TOKEN   KIZUNA の scrape_ingest_tokens に登録した合言葉（秘密。必須）
  KIZUNA_SUPABASE_URL   省略可（既定値は下の DEFAULT_URL）
  KIZUNA_ANON_KEY       省略可（既定値は下の DEFAULT_ANON_KEY）
合言葉が未設定なら何もしない。送れなくても収集全体は止めない（ログに警告を出す）。

URL と anon キーは KIZUNA の画面のソース（https://kizuna-crm.pages.dev/）にも載っている公開用の値なので、
既定値としてコードに置く（秘密ではない。service_role / secret キーは絶対に置かない）。
"""
import json
import logging
import os
import urllib.error
import urllib.request
from datetime import timezone, datetime

logger = logging.getLogger(__name__)

CHUNK = 500

DEFAULT_URL = "https://tlebenzxotboyvrfdsod.supabase.co"
DEFAULT_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRsZWJlbnp4b3Rib3l2cmZkc29kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4MTI4NTUsImV4cCI6MjA5MjM4ODg1NX0."
    "nA49xIDB76Ummbh9ZCxlhqaHpyH25JkGwoNENduUf8c"
)


def _iso_utc(s: str) -> str:
    """collected_at（GitHub Actions はUTCで動くためタイムゾーン無しの時刻）をUTCとして明示する。"""
    if not s:
        return ""
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _rows(leads) -> list[dict]:
    return [
        {
            "company_name": l.company_name,
            "legal_name": l.legal_name or "",
            "corporate_number": l.corporate_number or "",
            "address": l.address or "",
            "phone": l.phone or "",
            "phone_source": getattr(l, "phone_source", "") or "",
            "industry": l.industry or "",
            "source": l.source_site,
            "collected_at": _iso_utc(l.collected_at),
        }
        for l in leads
    ]


def push_to_kizuna(leads, batch: str) -> int:
    url = ((os.environ.get("KIZUNA_SUPABASE_URL") or "").strip() or DEFAULT_URL).rstrip("/")
    key = (os.environ.get("KIZUNA_ANON_KEY") or "").strip() or DEFAULT_ANON_KEY
    token = (os.environ.get("KIZUNA_INGEST_TOKEN") or "").strip()
    if not token:
        logger.info("[KIZUNA] 合言葉（KIZUNA_INGEST_TOKEN）が未設定のためスキップ")
        return 0
    if not leads:
        return 0

    rows = _rows(leads)
    added = 0
    for i in range(0, len(rows), CHUNK):
        body = json.dumps({"p_token": token, "p_batch": batch, "p_rows": rows[i:i + CHUNK]}).encode()
        req = urllib.request.Request(
            f"{url}/rest/v1/rpc/scrape_stage_push",
            data=body,
            method="POST",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                added += int(json.loads(resp.read() or b"0") or 0)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            logger.error(f"[KIZUNA] 送信に失敗しました（HTTP {e.code}）: {detail}")
            print(f"::warning title=KIZUNAへの送信失敗::HTTP {e.code} {detail}")
            return added
        except Exception as e:
            logger.error(f"[KIZUNA] 送信に失敗しました: {e}")
            print(f"::warning title=KIZUNAへの送信失敗::{e}")
            return added

    with_phone = sum(1 for r in rows if r["phone"])
    logger.info(f"[KIZUNA] 取込待ちに {added}件 追加（送信 {len(rows)}件・電話番号あり {with_phone}件・週 {batch}）")
    print(f"::notice title=KIZUNA取込待ち::{batch} に {added}件 追加（送信 {len(rows)}件・電話番号あり {with_phone}件）")
    return added
