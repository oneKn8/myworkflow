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
    content_hash TEXT NOT NULL,
    subreddit TEXT,
    scheduled_at TEXT,
    posted_at TEXT,
    post_url TEXT,
    status TEXT DEFAULT 'queued' CHECK(status IN ('queued', 'needs_review', 'approved', 'posted', 'failed', 'cancelled')),
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_queue_idempotency
    ON social_queue(platform, post_slug, content_hash)
    WHERE status != 'cancelled';

CREATE INDEX IF NOT EXISTS idx_queue_status_scheduled
    ON social_queue(status, scheduled_at);

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

CREATE TABLE IF NOT EXISTS content_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    platform TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    platform_post_id TEXT,
    platform_url TEXT,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'queued', 'needs_review', 'approved', 'posted', 'failed')),
    views INTEGER DEFAULT 0,
    reactions INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    published_at TEXT,
    metrics_updated_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(slug, platform)
);

CREATE TABLE IF NOT EXISTS platform_rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    last_posted_at TEXT NOT NULL,
    UNIQUE(platform)
);
"""


MIGRATIONS = [
    # Add content_hash to existing social_queue tables that lack it
    """ALTER TABLE social_queue ADD COLUMN content_hash TEXT DEFAULT '' NOT NULL""",
    # Add needs_review and approved to status CHECK -- SQLite can't alter CHECK constraints,
    # but the CREATE TABLE above handles new installs. For existing DBs, the CHECK is soft.
]


def init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection) -> None:
    for sql in MIGRATIONS:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # column/table already exists


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
