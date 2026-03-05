"""Single SQLite database for all myworkflow tables."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    local_path TEXT NOT NULL,
    devto_url TEXT,
    devto_id INTEGER,
    hashnode_url TEXT,
    hashnode_id TEXT,
    canonical_url TEXT,
    published_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS social_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_slug TEXT NOT NULL,
    platform TEXT NOT NULL,
    content TEXT NOT NULL,
    scheduled_at TEXT,
    posted_at TEXT,
    post_url TEXT,
    status TEXT DEFAULT 'queued' CHECK(status IN ('queued', 'posted', 'failed', 'cancelled')),
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    confirmed INTEGER DEFAULT 0,
    confirm_token TEXT,
    unsubscribe_token TEXT,
    subscribed_at TEXT DEFAULT (datetime('now')),
    confirmed_at TEXT,
    unsubscribed_at TEXT
);

CREATE TABLE IF NOT EXISTS editions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    subject TEXT NOT NULL,
    html_body TEXT NOT NULL,
    sent_at TEXT,
    recipient_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS send_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edition_id INTEGER NOT NULL REFERENCES editions(id),
    subscriber_id INTEGER NOT NULL REFERENCES subscribers(id),
    resend_id TEXT,
    status TEXT DEFAULT 'sent' CHECK(status IN ('sent', 'delivered', 'bounced', 'failed')),
    sent_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_db(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    if not db_path.exists():
        init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
