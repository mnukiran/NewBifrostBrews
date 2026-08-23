"""SQLite helpers.

WAL lets readers proceed while a write is in flight, which matters once
the site takes concurrent traffic on the phone.
"""
import sqlite3
from contextlib import contextmanager

from app.config import BASE_DIR, DB_PATH

SCHEMA_PATH = BASE_DIR.parent / "db" / "schema.sql"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


DEFAULT_CATEGORIES = [
    ("general", "General", "Anything and everything.", 0),
    ("courses", "Course talk", "Discuss the Gen AI courses on the site.", 1),
    ("water-cooler", "Water cooler", "Off-topic chatter and gossip.", 2),
]


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO categories (slug, name, description, sort) VALUES (?, ?, ?, ?)",
                DEFAULT_CATEGORIES,
            )
