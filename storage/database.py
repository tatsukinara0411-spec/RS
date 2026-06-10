import sqlite3
import os
from models.lead import Lead
from utils.fingerprint import compute_fingerprint

DB_PATH = os.environ.get("DB_PATH", "./data/leads.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_companies (
            fingerprint TEXT PRIMARY KEY,
            company_name TEXT,
            first_seen_at TEXT,
            source_site TEXT
        )
    """)
    conn.commit()
    conn.close()


def is_seen(company_name: str, address: str) -> bool:
    fp = compute_fingerprint(company_name, address)
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT 1 FROM seen_companies WHERE fingerprint = ?", (fp,)
    ).fetchone()
    conn.close()
    return row is not None


def mark_seen(lead: Lead):
    fp = compute_fingerprint(lead.company_name, lead.address)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen_companies (fingerprint, company_name, first_seen_at, source_site) VALUES (?, ?, ?, ?)",
        (fp, lead.company_name, lead.collected_at, lead.source_site),
    )
    conn.commit()
    conn.close()


def deduplicate(leads: list[Lead]) -> list[Lead]:
    seen_fps = set()
    result = []
    for lead in leads:
        fp = compute_fingerprint(lead.company_name, lead.address)
        if fp not in seen_fps and not is_seen(lead.company_name, lead.address):
            seen_fps.add(fp)
            result.append(lead)
    return result
