"""Per-platform rate limiting and backoff."""

import time
import random
import sqlite3
from datetime import datetime, timedelta


# Minimum seconds between posts per platform
PLATFORM_PACING = {
    "twitter": 120,      # 2 min -- free tier is tight
    "linkedin": 600,     # 10 min -- they shadowban fast
    "reddit": 900,       # 15 min -- human-like cadence
}

MAX_RETRIES = 3
BASE_BACKOFF = 2.0  # seconds


def check_pacing(db: sqlite3.Connection, platform: str) -> tuple[bool, int]:
    """Check if enough time has passed since last post on this platform.
    Returns (can_post, seconds_to_wait).
    """
    min_gap = PLATFORM_PACING.get(platform, 60)

    row = db.execute(
        "SELECT last_posted_at FROM platform_rate_limits WHERE platform = ?",
        (platform,),
    ).fetchone()

    if not row:
        return True, 0

    last_posted = datetime.fromisoformat(row["last_posted_at"])
    elapsed = (datetime.now() - last_posted).total_seconds()
    remaining = min_gap - elapsed

    if remaining <= 0:
        return True, 0

    return False, int(remaining)


def record_post(db: sqlite3.Connection, platform: str) -> None:
    """Record that we just posted to this platform."""
    now = datetime.now().isoformat()
    db.execute(
        """INSERT INTO platform_rate_limits (platform, last_posted_at)
           VALUES (?, ?)
           ON CONFLICT(platform) DO UPDATE SET last_posted_at = ?""",
        (platform, now, now),
    )


def backoff_with_jitter(attempt: int) -> float:
    """Exponential backoff with jitter. Returns seconds to sleep."""
    delay = BASE_BACKOFF * (2 ** (attempt - 1))
    jitter = random.uniform(0, delay * 0.5)
    return delay + jitter


def retry_with_backoff(func, max_retries: int = MAX_RETRIES):
    """Call func(), retrying on exception with exponential backoff + jitter."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = backoff_with_jitter(attempt)
                time.sleep(delay)
    raise last_error
