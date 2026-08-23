"""SQLite helpers. Unused until Phase 2 (courses) — kept minimal.

WAL lets forum readers proceed while a write is in flight, which matters
once the site takes concurrent traffic on the phone.
"""
import sqlite3

from app.config import DB_PATH


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
