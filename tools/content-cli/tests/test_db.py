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
