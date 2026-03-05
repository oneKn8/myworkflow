"""Tests for rate limiting."""

import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from myworkflow.db import init_db, get_db
from myworkflow.shared.ratelimit import check_pacing, record_post, backoff_with_jitter


def test_check_pacing_no_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            can_post, wait = check_pacing(db, "twitter")
            assert can_post is True
            assert wait == 0


def test_check_pacing_recent_post():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        with get_db(db_path) as db:
            record_post(db, "twitter")

        with get_db(db_path) as db:
            can_post, wait = check_pacing(db, "twitter")
            assert can_post is False
            assert wait > 0


def test_check_pacing_old_post():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_db(db_path)

        old_time = (datetime.now() - timedelta(minutes=30)).isoformat()
        with get_db(db_path) as db:
            db.execute(
                """INSERT INTO platform_rate_limits (platform, last_posted_at)
                   VALUES ('twitter', ?)""",
                (old_time,),
            )

        with get_db(db_path) as db:
            can_post, wait = check_pacing(db, "twitter")
            assert can_post is True


def test_backoff_with_jitter():
    delay1 = backoff_with_jitter(1)
    delay2 = backoff_with_jitter(2)
    delay3 = backoff_with_jitter(3)
    # Each attempt should have a larger base delay
    assert delay1 < 10
    assert delay2 > delay1 * 0.5  # jitter makes this probabilistic, but base doubles
    assert delay3 > delay2 * 0.5
