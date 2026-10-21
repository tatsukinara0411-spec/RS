"""
外部API（Google Places）の呼び出し回数を月単位で記録し、予算超過を防ぐ。

カウンタは重複除外用のSQLite（GitHub Actionsのキャッシュで実行間に引き継がれる）に保存する。
"""
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "./data/leads.db")

# 1件の会社を調べるのに Find Place + Place Details の2回呼ぶ想定の概算単価（円）
COST_PER_LOOKUP_JPY = 5


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS api_usage ("
        "  ym TEXT PRIMARY KEY,"
        "  lookups INTEGER NOT NULL DEFAULT 0"
        ")"
    )
    conn.commit()
    return conn


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def get_month_lookups(ym: str | None = None) -> int:
    ym = ym or current_month()
    conn = _conn()
    row = conn.execute("SELECT lookups FROM api_usage WHERE ym = ?", (ym,)).fetchone()
    conn.close()
    return row[0] if row else 0


def add_month_lookups(n: int, ym: str | None = None) -> int:
    """今月の呼び出し数に n を加算し、加算後の合計を返す。"""
    if n <= 0:
        return get_month_lookups(ym)
    ym = ym or current_month()
    conn = _conn()
    conn.execute(
        "INSERT INTO api_usage (ym, lookups) VALUES (?, ?) "
        "ON CONFLICT(ym) DO UPDATE SET lookups = lookups + excluded.lookups",
        (ym, n),
    )
    conn.commit()
    conn.close()
    return get_month_lookups(ym)


def notify(message: str) -> None:
    """ワークフローの実行結果ページに目立つ形で残す。"""
    logger.warning(message)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(message + "\n\n")
        except Exception:
            pass


def budget_status(monthly_budget: int, ym: str | None = None) -> tuple[int, int, float]:
    """(今月の利用数, 残り, 使用率%) を返す。"""
    used = get_month_lookups(ym)
    remaining = max(0, monthly_budget - used)
    pct = (used / monthly_budget * 100) if monthly_budget > 0 else 0.0
    return used, remaining, pct
