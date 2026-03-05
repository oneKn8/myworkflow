"""Tests for database operations."""

import tempfile
from pathlib import Path

from myworkflow.db import init_db, get_db


def test_init_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)
        assert db_path.exists()


def test_insert_and_read_post():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                "INSERT INTO posts (slug, title, local_path, canonical_url) VALUES (?, ?, ?, ?)",
                ("test-post", "Test Post", "/tmp/test.md", "https://example.com/blog/test-post"),
            )

        with get_db(db_path) as db:
            row = db.execute("SELECT * FROM posts WHERE slug = ?", ("test-post",)).fetchone()
            assert row["title"] == "Test Post"
            assert row["canonical_url"] == "https://example.com/blog/test-post"


def test_subscriber_table():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                "INSERT INTO subscribers (email, confirm_token) VALUES (?, ?)",
                ("test@example.com", "abc123"),
            )

        with get_db(db_path) as db:
            row = db.execute("SELECT * FROM subscribers WHERE email = ?", ("test@example.com",)).fetchone()
            assert row["confirmed"] == 0
            assert row["confirm_token"] == "abc123"


def test_social_queue_idempotency():
    """Fix 1: Duplicate content_hash + platform + slug should be rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO social_queue (post_slug, platform, content, content_hash, status)
                   VALUES (?, ?, ?, ?, 'queued')""",
                ("my-post", "twitter", "Hello world", "abc123"),
            )

        # Same content_hash + platform + slug should fail
        import sqlite3
        try:
            with get_db(db_path) as db:
                db.execute(
                    """INSERT INTO social_queue (post_slug, platform, content, content_hash, status)
                       VALUES (?, ?, ?, ?, 'queued')""",
                    ("my-post", "twitter", "Hello world", "abc123"),
                )
            assert False, "Should have raised IntegrityError"
        except sqlite3.IntegrityError:
            pass

        # Cancelled items don't block re-enqueue
        with get_db(db_path) as db:
            db.execute("UPDATE social_queue SET status = 'cancelled' WHERE content_hash = 'abc123'")

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO social_queue (post_slug, platform, content, content_hash, status)
                   VALUES (?, ?, ?, ?, 'queued')""",
                ("my-post", "twitter", "Hello world", "abc123"),
            )
            count = db.execute("SELECT COUNT(*) FROM social_queue WHERE post_slug = 'my-post'").fetchone()[0]
            assert count == 2  # one cancelled, one queued


def test_social_queue_review_status():
    """Fix 3: needs_review and approved statuses work."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO social_queue (post_slug, platform, content, content_hash, status)
                   VALUES (?, ?, ?, ?, 'needs_review')""",
                ("my-post", "linkedin", "Some post", "def456"),
            )

        with get_db(db_path) as db:
            row = db.execute("SELECT * FROM social_queue WHERE content_hash = 'def456'").fetchone()
            assert row["status"] == "needs_review"

            db.execute("UPDATE social_queue SET status = 'approved' WHERE id = ?", (row["id"],))

        with get_db(db_path) as db:
            row = db.execute("SELECT * FROM social_queue WHERE content_hash = 'def456'").fetchone()
            assert row["status"] == "approved"


def test_social_queue_with_attempts():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO social_queue (post_slug, platform, content, content_hash, subreddit, scheduled_at, status, attempts)
                   VALUES (?, ?, ?, ?, ?, ?, 'queued', 0)""",
                ("test-post", "twitter", "Hello world", "hash1", None, None),
            )

        with get_db(db_path) as db:
            row = db.execute("SELECT * FROM social_queue WHERE post_slug = ?", ("test-post",)).fetchone()
            assert row["platform"] == "twitter"
            assert row["attempts"] == 0
            assert row["status"] == "queued"


def test_content_ledger():
    """Content ledger tracks posts across platforms."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO content_ledger (slug, platform, canonical_url, status)
                   VALUES (?, ?, ?, 'draft')""",
                ("my-post", "twitter", "https://example.com/blog/my-post"),
            )
            db.execute(
                """INSERT INTO content_ledger (slug, platform, canonical_url, status)
                   VALUES (?, ?, ?, 'needs_review')""",
                ("my-post", "linkedin", "https://example.com/blog/my-post"),
            )

        with get_db(db_path) as db:
            rows = db.execute("SELECT * FROM content_ledger WHERE slug = 'my-post' ORDER BY platform").fetchall()
            assert len(rows) == 2
            assert rows[0]["platform"] == "linkedin"
            assert rows[0]["status"] == "needs_review"
            assert rows[1]["platform"] == "twitter"
            assert rows[1]["status"] == "draft"


def test_content_ledger_unique_slug_platform():
    """Ledger enforces one entry per slug+platform."""
    import sqlite3
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO content_ledger (slug, platform, canonical_url, status)
                   VALUES (?, ?, ?, 'posted')""",
                ("my-post", "twitter", "https://example.com/blog/my-post"),
            )

        try:
            with get_db(db_path) as db:
                db.execute(
                    """INSERT INTO content_ledger (slug, platform, canonical_url, status)
                       VALUES (?, ?, ?, 'draft')""",
                    ("my-post", "twitter", "https://example.com/blog/my-post"),
                )
            assert False, "Should have raised IntegrityError"
        except sqlite3.IntegrityError:
            pass


def test_platform_rate_limits():
    """Rate limit table tracks last post per platform."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO platform_rate_limits (platform, last_posted_at)
                   VALUES ('twitter', datetime('now'))
                   ON CONFLICT(platform) DO UPDATE SET last_posted_at = datetime('now')""",
            )

        with get_db(db_path) as db:
            row = db.execute("SELECT * FROM platform_rate_limits WHERE platform = 'twitter'").fetchone()
            assert row is not None
            assert row["last_posted_at"] is not None
