"""myworkflow CLI -- unified content automation."""

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from myworkflow.config import load_config
from myworkflow.db import get_db, init_db
from myworkflow.sanitize import load_post, sanitize_for_devto, sanitize_for_hashnode
from myworkflow.shared.logging import success, error, info, warn
from myworkflow.shared.utm import add_utm, inject_utm_into_content
from myworkflow.shared.ratelimit import check_pacing, record_post, retry_with_backoff

app = typer.Typer(
    name="myworkflow",
    help="Content automation CLI -- cross-post, repurpose, social, newsletter.",
    no_args_is_help=True,
)
console = Console()

# --- Subcommand groups ---
cross_post_app = typer.Typer(help="Cross-post blog articles to Dev.to and Hashnode.")
social_app = typer.Typer(help="Social media queue management.")
newsletter_app = typer.Typer(help="Newsletter management and API server.")
repurpose_app = typer.Typer(help="Repurpose blog posts into social content.")
ledger_app = typer.Typer(help="Content ledger -- track posts across platforms.")

app.add_typer(cross_post_app, name="cross-post")
app.add_typer(social_app, name="social")
app.add_typer(newsletter_app, name="newsletter")
app.add_typer(repurpose_app, name="repurpose")
app.add_typer(ledger_app, name="ledger")


def _content_hash(content: str) -> str:
    """SHA256 of content for idempotency."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ===== CROSS-POST =====


@cross_post_app.command("publish")
def cross_post_publish(
    path: Path = typer.Argument(..., help="Path to markdown/MDX file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without publishing"),
    platform: str = typer.Option("all", help="Platform: devto, hashnode, or all"),
):
    """Cross-post a blog article to Dev.to and/or Hashnode."""
    config = load_config()
    meta, body = load_post(path)

    title = meta.get("title", "Untitled")
    tags = meta.get("tags", [])
    slug = path.stem
    canonical = f"{config.blog_url}/blog/{slug}"

    if dry_run:
        info(f"Title: {title}")
        info(f"Canonical: {canonical}")
        info(f"Tags: {', '.join(tags)}")
        console.print("\n[bold]Sanitized body (Dev.to):[/bold]")
        console.print(sanitize_for_devto(body, canonical)[:500] + "...")
        return

    # Fix 1: Check idempotency -- skip if already posted to this platform
    with get_db(config.db_path) as db:
        existing = db.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()

    results = {}

    if platform in ("all", "devto"):
        if existing and existing["devto_url"]:
            info(f"Dev.to: already posted -> {existing['devto_url']}")
        elif not config.devto_api_key:
            error("DEVTO_API_KEY not set")
        else:
            from myworkflow.platforms.devto import publish_article

            sanitized = sanitize_for_devto(body, canonical)
            result = retry_with_backoff(lambda: publish_article(
                api_key=config.devto_api_key,
                title=title,
                body_markdown=sanitized,
                tags=tags,
                canonical_url=canonical,
            ))
            results["devto"] = result
            success(f"Dev.to: {result['url']}")

    if platform in ("all", "hashnode"):
        if existing and existing["hashnode_url"]:
            info(f"Hashnode: already posted -> {existing['hashnode_url']}")
        elif not config.hashnode_api_key or not config.hashnode_publication_id:
            error("HASHNODE_API_KEY or HASHNODE_PUBLICATION_ID not set")
        else:
            from myworkflow.platforms.hashnode import publish_article

            sanitized = sanitize_for_hashnode(body, canonical)
            result = retry_with_backoff(lambda: publish_article(
                api_key=config.hashnode_api_key,
                publication_id=config.hashnode_publication_id,
                title=title,
                body_markdown=sanitized,
                tags=tags,
                canonical_url=canonical,
            ))
            results["hashnode"] = result
            success(f"Hashnode: {result['url']}")

    if not results:
        return

    # Track in DB
    with get_db(config.db_path) as db:
        db.execute(
            """INSERT INTO posts (slug, title, local_path, devto_url, devto_id, hashnode_url, hashnode_id, canonical_url, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET
                   devto_url = COALESCE(excluded.devto_url, posts.devto_url),
                   devto_id = COALESCE(excluded.devto_id, posts.devto_id),
                   hashnode_url = COALESCE(excluded.hashnode_url, posts.hashnode_url),
                   hashnode_id = COALESCE(excluded.hashnode_id, posts.hashnode_id),
                   updated_at = datetime('now')""",
            (
                slug,
                title,
                str(path),
                results.get("devto", {}).get("url"),
                results.get("devto", {}).get("id"),
                results.get("hashnode", {}).get("url"),
                results.get("hashnode", {}).get("id"),
                canonical,
                datetime.now().isoformat(),
            ),
        )

        # Update content ledger
        for plat, result in results.items():
            db.execute(
                """INSERT INTO content_ledger (slug, platform, canonical_url, platform_post_id, platform_url, status, published_at)
                   VALUES (?, ?, ?, ?, ?, 'posted', datetime('now'))
                   ON CONFLICT(slug, platform) DO UPDATE SET
                       platform_post_id = excluded.platform_post_id,
                       platform_url = excluded.platform_url,
                       status = 'posted',
                       published_at = datetime('now')""",
                (slug, plat, canonical, result.get("id"), result.get("url")),
            )


@cross_post_app.command("status")
def cross_post_status(slug: str = typer.Argument(..., help="Post slug")):
    """Check cross-post status for a post."""
    config = load_config()
    with get_db(config.db_path) as db:
        row = db.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
        if not row:
            error(f"No record for slug: {slug}")
            raise typer.Exit(1)

        table = Table(title=f"Cross-post: {row['title']}")
        table.add_column("Field")
        table.add_column("Value")
        for key in row.keys():
            table.add_row(key, str(row[key] or ""))
        console.print(table)


# ===== REPURPOSE =====


@repurpose_app.command("generate")
def repurpose_generate(
    path: Path = typer.Argument(..., help="Path to markdown/MDX file"),
    format: str = typer.Option("all", help="Format: twitter, linkedin, reddit, devto-teaser, or all"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    enqueue: bool = typer.Option(False, "--enqueue", help="Add to social queue"),
    at: Optional[str] = typer.Option(None, "--at", help="Schedule time (YYYY-MM-DD HH:MM)"),
):
    """Generate social content from a blog post using AI."""
    config = load_config()
    if not config.anthropic_api_key:
        error("ANTHROPIC_API_KEY not set")
        raise typer.Exit(1)

    meta, body = load_post(path)
    title = meta.get("title", "Untitled")
    slug = path.stem
    blog_url = f"{config.blog_url}/blog/{slug}"

    from myworkflow.repurpose.engine import repurpose, repurpose_all, FORMATS

    if format == "all":
        results = repurpose_all(config.anthropic_api_key, title, body, blog_url)
    else:
        results = {format: repurpose(config.anthropic_api_key, title, body, format, blog_url)}

    for fmt, content in results.items():
        # Fix 5: Inject UTM tags into all blog URLs in generated content
        content = inject_utm_into_content(content, blog_url, platform=fmt, slug=slug)

        console.print(f"\n[bold cyan]--- {fmt.upper()} ---[/bold cyan]")
        console.print(content)

        if output:
            output.mkdir(parents=True, exist_ok=True)
            (output / f"{slug}-{fmt}.txt").write_text(content)
            info(f"Saved: {output / f'{slug}-{fmt}.txt'}")

        if enqueue and fmt in ("twitter", "linkedin", "reddit"):
            chash = _content_hash(content)

            # Fix 3: LinkedIn and Reddit go to needs_review, Twitter auto-queues
            initial_status = "queued" if fmt == "twitter" else "needs_review"

            with get_db(config.db_path) as db:
                # Fix 1: Idempotency -- skip if duplicate
                existing = db.execute(
                    """SELECT id, status FROM social_queue
                       WHERE platform = ? AND post_slug = ? AND content_hash = ?
                       AND status != 'cancelled'""",
                    (fmt, slug, chash),
                ).fetchone()

                if existing:
                    info(f"Skipped {fmt}: already enqueued (id={existing['id']}, status={existing['status']})")
                    continue

                db.execute(
                    """INSERT INTO social_queue (post_slug, platform, content, content_hash, subreddit, scheduled_at, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (slug, fmt, content, chash, None, at, initial_status),
                )

                # Update content ledger
                canonical = f"{config.blog_url}/blog/{slug}"
                db.execute(
                    """INSERT INTO content_ledger (slug, platform, canonical_url, status)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(slug, platform) DO UPDATE SET status = excluded.status""",
                    (slug, fmt, canonical, initial_status),
                )

            if initial_status == "needs_review":
                warn(f"Enqueued {fmt} as NEEDS REVIEW -- approve with: myworkflow social approve <id>")
            else:
                success(f"Enqueued {fmt} post" + (f" for {at}" if at else ""))


# ===== SOCIAL =====


@social_app.command("list")
def social_list(
    status_filter: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
):
    """List queued social posts."""
    config = load_config()
    with get_db(config.db_path) as db:
        if status_filter:
            rows = db.execute(
                "SELECT * FROM social_queue WHERE status = ? ORDER BY created_at DESC LIMIT 30",
                (status_filter,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM social_queue ORDER BY created_at DESC LIMIT 30"
            ).fetchall()

    if not rows:
        info("No queued posts")
        return

    table = Table(title="Social Queue")
    table.add_column("ID")
    table.add_column("Slug")
    table.add_column("Platform")
    table.add_column("Status")
    table.add_column("Attempts")
    table.add_column("Scheduled")
    table.add_column("Content", max_width=40)

    for row in rows:
        status_str = row["status"]
        if status_str == "needs_review":
            status_str = "[yellow]needs_review[/yellow]"
        elif status_str == "posted":
            status_str = "[green]posted[/green]"
        elif status_str == "failed":
            status_str = "[red]failed[/red]"

        table.add_row(
            str(row["id"]),
            row["post_slug"],
            row["platform"],
            status_str,
            str(row["attempts"]),
            row["scheduled_at"] or "now",
            (row["content"][:37] + "...") if len(row["content"]) > 40 else row["content"],
        )
    console.print(table)


@social_app.command("enqueue")
def social_enqueue(
    slug: str = typer.Argument(..., help="Post slug"),
    platform: str = typer.Argument(..., help="Platform: twitter, linkedin, reddit"),
    content: str = typer.Argument(..., help="Post content"),
    at: Optional[str] = typer.Option(None, "--at", help="Schedule time"),
    subreddit: Optional[str] = typer.Option(None, "--subreddit", help="Reddit subreddit"),
    auto: bool = typer.Option(False, "--auto", help="Skip review gate (auto-approve)"),
):
    """Manually enqueue a social post."""
    config = load_config()
    chash = _content_hash(content)

    # Fix 3: Review gate for LinkedIn/Reddit unless --auto
    initial_status = "queued"
    if not auto and platform in ("linkedin", "reddit"):
        initial_status = "needs_review"

    with get_db(config.db_path) as db:
        existing = db.execute(
            """SELECT id FROM social_queue
               WHERE platform = ? AND post_slug = ? AND content_hash = ?
               AND status != 'cancelled'""",
            (platform, slug, chash),
        ).fetchone()

        if existing:
            info(f"Duplicate detected (id={existing['id']}), skipping")
            return

        db.execute(
            """INSERT INTO social_queue (post_slug, platform, content, content_hash, subreddit, scheduled_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (slug, platform, content, chash, subreddit, at, initial_status),
        )

    if initial_status == "needs_review":
        warn(f"Enqueued {platform} as NEEDS REVIEW -- approve with: myworkflow social approve <id>")
    else:
        success(f"Enqueued {platform} post for {slug}")


@social_app.command("approve")
def social_approve(
    queue_id: int = typer.Argument(..., help="Queue item ID to approve"),
):
    """Approve a needs_review post for posting."""
    config = load_config()
    with get_db(config.db_path) as db:
        row = db.execute("SELECT * FROM social_queue WHERE id = ?", (queue_id,)).fetchone()
        if not row:
            error(f"Queue item {queue_id} not found")
            raise typer.Exit(1)
        if row["status"] != "needs_review":
            error(f"Item {queue_id} is '{row['status']}', not needs_review")
            raise typer.Exit(1)

        # Show content for review
        console.print(f"\n[bold]{row['platform'].upper()}[/bold] for [cyan]{row['post_slug']}[/cyan]:")
        console.print(row["content"])
        console.print()

        db.execute(
            "UPDATE social_queue SET status = 'approved' WHERE id = ?",
            (queue_id,),
        )

        # Update ledger
        db.execute(
            """UPDATE content_ledger SET status = 'approved'
               WHERE slug = ? AND platform = ?""",
            (row["post_slug"], row["platform"]),
        )

    success(f"Approved item {queue_id} -- will post on next drain")


@social_app.command("review")
def social_review():
    """Show all posts awaiting review."""
    config = load_config()
    with get_db(config.db_path) as db:
        rows = db.execute(
            "SELECT * FROM social_queue WHERE status = 'needs_review' ORDER BY created_at"
        ).fetchall()

    if not rows:
        info("No posts waiting for review")
        return

    for row in rows:
        console.print(f"\n[bold]ID {row['id']}[/bold] | [cyan]{row['platform']}[/cyan] | {row['post_slug']}")
        console.print("-" * 50)
        console.print(row["content"])
        console.print()

    info(f"{len(rows)} post(s) awaiting review. Approve with: myworkflow social approve <id>")


@social_app.command("drain")
def social_drain():
    """Process and post all approved/queued (and due) social posts."""
    config = load_config()
    now = datetime.now().isoformat()
    max_attempts = 3

    # Fix 3: Only drain 'queued' and 'approved' (not 'needs_review')
    with get_db(config.db_path) as db:
        rows = db.execute(
            """SELECT * FROM social_queue
               WHERE status IN ('queued', 'approved')
               AND attempts < ?
               AND (scheduled_at IS NULL OR scheduled_at <= ?)
               ORDER BY created_at""",
            (max_attempts, now),
        ).fetchall()

    if not rows:
        info("Nothing to drain")
        return

    posted = 0
    skipped = 0
    failed = 0

    for row in rows:
        platform = row["platform"]
        content = row["content"]
        post_id = row["id"]
        attempt = row["attempts"] + 1

        # Fix 2: Check per-platform pacing
        with get_db(config.db_path) as db:
            can_post, wait_secs = check_pacing(db, platform)

        if not can_post:
            info(f"Rate limited on {platform}, wait {wait_secs}s -- skipping id={post_id}")
            skipped += 1
            continue

        info(f"Posting to {platform} (attempt {attempt}/{max_attempts})...")

        try:
            # Fix 5: UTM tags injected at post time
            slug = row["post_slug"]
            blog_url = f"{config.blog_url}/blog/{slug}"
            tagged_content = inject_utm_into_content(content, blog_url, platform=platform, slug=slug)

            post_url = _post_to_platform(config, platform, tagged_content, row)

            with get_db(config.db_path) as db:
                db.execute(
                    """UPDATE social_queue
                       SET status = 'posted', posted_at = datetime('now'),
                           post_url = ?, attempts = ?
                       WHERE id = ?""",
                    (post_url, attempt, post_id),
                )
                # Fix 2: Record post time for pacing
                record_post(db, platform)

                # Update content ledger
                db.execute(
                    """UPDATE content_ledger
                       SET status = 'posted', platform_url = ?, published_at = datetime('now')
                       WHERE slug = ? AND platform = ?""",
                    (post_url, slug, platform),
                )

            success(f"Posted to {platform}: {post_url}")
            posted += 1

        except Exception as e:
            new_status = "failed" if attempt >= max_attempts else "approved"
            with get_db(config.db_path) as db:
                db.execute(
                    """UPDATE social_queue
                       SET status = ?, error_message = ?, attempts = ?
                       WHERE id = ?""",
                    (new_status, str(e), attempt, post_id),
                )
            if new_status == "failed":
                error(f"Permanently failed {platform}: {e}")

                with get_db(config.db_path) as db:
                    db.execute(
                        "UPDATE content_ledger SET status = 'failed' WHERE slug = ? AND platform = ?",
                        (row["post_slug"], platform),
                    )
            else:
                warn(f"Retry later {platform} (attempt {attempt}): {e}")
            failed += 1

    info(f"Drain complete: {posted} posted, {skipped} rate-limited, {failed} failed")


@social_app.command("cancel")
def social_cancel(
    queue_id: int = typer.Argument(..., help="Queue item ID"),
):
    """Cancel a queued social post."""
    config = load_config()
    with get_db(config.db_path) as db:
        db.execute(
            "UPDATE social_queue SET status = 'cancelled' WHERE id = ? AND status IN ('queued', 'needs_review', 'approved')",
            (queue_id,),
        )
    success(f"Cancelled queue item {queue_id}")


@social_app.command("retry")
def social_retry(
    queue_id: int = typer.Argument(..., help="Queue item ID"),
):
    """Reset a failed post back to approved for retry."""
    config = load_config()
    with get_db(config.db_path) as db:
        db.execute(
            "UPDATE social_queue SET status = 'approved', attempts = 0, error_message = NULL WHERE id = ? AND status = 'failed'",
            (queue_id,),
        )
    success(f"Reset queue item {queue_id} for retry")


def _post_to_platform(config, platform: str, content: str, row) -> str:
    """Dispatch to the appropriate platform API."""
    slug = row["post_slug"]
    blog_url = f"{config.blog_url}/blog/{slug}"

    if platform == "twitter":
        if not all([config.twitter_consumer_key, config.twitter_consumer_secret,
                     config.twitter_access_token, config.twitter_access_token_secret]):
            raise ValueError("Twitter OAuth credentials not configured")

        from myworkflow.platforms.twitter import post_tweet, post_thread

        tweets = [t.strip() for t in content.split("---") if t.strip()]
        if len(tweets) > 1:
            results = post_thread(
                config.twitter_consumer_key, config.twitter_consumer_secret,
                config.twitter_access_token, config.twitter_access_token_secret,
                tweets,
            )
            return results[-1]["url"]
        else:
            result = post_tweet(
                config.twitter_consumer_key, config.twitter_consumer_secret,
                config.twitter_access_token, config.twitter_access_token_secret,
                tweets[0],
            )
            return result["url"]

    elif platform == "linkedin":
        if not config.linkedin_access_token or not config.linkedin_person_id:
            raise ValueError("LinkedIn credentials not configured")

        from myworkflow.platforms.linkedin import post_update

        result = post_update(
            config.linkedin_access_token,
            config.linkedin_person_id,
            content,
            article_url=add_utm(blog_url, source="linkedin", slug=slug),
        )
        return result["url"]

    elif platform == "reddit":
        if not all([config.reddit_client_id, config.reddit_client_secret,
                     config.reddit_username, config.reddit_password]):
            raise ValueError("Reddit credentials not configured")

        from myworkflow.platforms.reddit import get_access_token, submit_selftext

        subreddit = row["subreddit"] or config.reddit_default_subreddit
        if not subreddit:
            raise ValueError("No subreddit specified (use --subreddit or set REDDIT_DEFAULT_SUBREDDIT)")

        token = get_access_token(
            config.reddit_client_id, config.reddit_client_secret,
            config.reddit_username, config.reddit_password,
        )

        title = slug.replace("-", " ").title()
        body = content
        if "TITLE:" in content and "BODY:" in content:
            parts = content.split("---", 1)
            title = parts[0].replace("TITLE:", "").strip()
            body = parts[1].replace("BODY:", "").strip() if len(parts) > 1 else content

        result = submit_selftext(token, subreddit, title, body)
        return result["url"]

    else:
        raise ValueError(f"Unknown platform: {platform}")


# ===== CONTENT LEDGER =====


@ledger_app.command("show")
def ledger_show(
    slug: Optional[str] = typer.Argument(None, help="Post slug (omit for all)"),
):
    """Show content ledger -- all posts across all platforms."""
    config = load_config()
    with get_db(config.db_path) as db:
        if slug:
            rows = db.execute(
                "SELECT * FROM content_ledger WHERE slug = ? ORDER BY platform",
                (slug,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM content_ledger ORDER BY slug, platform"
            ).fetchall()

    if not rows:
        info("Ledger is empty")
        return

    table = Table(title="Content Ledger")
    table.add_column("Slug")
    table.add_column("Platform")
    table.add_column("Status")
    table.add_column("URL", max_width=50)
    table.add_column("Views")
    table.add_column("Reactions")
    table.add_column("Published")

    for row in rows:
        status_str = row["status"]
        if status_str == "posted":
            status_str = "[green]posted[/green]"
        elif status_str == "needs_review":
            status_str = "[yellow]review[/yellow]"
        elif status_str == "failed":
            status_str = "[red]failed[/red]"

        table.add_row(
            row["slug"],
            row["platform"],
            status_str,
            row["platform_url"] or "-",
            str(row["views"]),
            str(row["reactions"]),
            row["published_at"] or "-",
        )
    console.print(table)


@ledger_app.command("best-platform")
def ledger_best_platform(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent posts"),
):
    """Show which platform performs best for your posts."""
    config = load_config()
    with get_db(config.db_path) as db:
        rows = db.execute(
            """SELECT platform,
                      COUNT(*) as post_count,
                      SUM(views) as total_views,
                      SUM(reactions) as total_reactions,
                      SUM(clicks) as total_clicks,
                      ROUND(AVG(views), 0) as avg_views,
                      ROUND(AVG(reactions), 0) as avg_reactions
               FROM content_ledger
               WHERE status = 'posted'
               GROUP BY platform
               ORDER BY total_views DESC""",
        ).fetchall()

    if not rows:
        info("No posted content in ledger yet")
        return

    table = Table(title=f"Platform Performance")
    table.add_column("Platform")
    table.add_column("Posts")
    table.add_column("Total Views")
    table.add_column("Avg Views")
    table.add_column("Total Reactions")
    table.add_column("Total Clicks")

    for row in rows:
        table.add_row(
            row["platform"],
            str(row["post_count"]),
            str(row["total_views"]),
            str(int(row["avg_views"] or 0)),
            str(row["total_reactions"]),
            str(row["total_clicks"]),
        )
    console.print(table)


@ledger_app.command("sync-metrics")
def ledger_sync_metrics():
    """Pull latest metrics from platforms into the ledger."""
    config = load_config()

    with get_db(config.db_path) as db:
        rows = db.execute(
            "SELECT * FROM content_ledger WHERE status = 'posted' AND platform_post_id IS NOT NULL"
        ).fetchall()

    if not rows:
        info("No posted content to sync")
        return

    synced = 0
    for row in rows:
        try:
            if row["platform"] == "devto" and config.devto_api_key:
                from myworkflow.platforms.devto import get_article_stats
                stats = get_article_stats(config.devto_api_key, int(row["platform_post_id"]))
                with get_db(config.db_path) as db:
                    db.execute(
                        """UPDATE content_ledger
                           SET views = ?, reactions = ?, comments = ?, metrics_updated_at = datetime('now')
                           WHERE id = ?""",
                        (stats["views"], stats["reactions"], stats["comments"], row["id"]),
                    )
                synced += 1
        except Exception as e:
            warn(f"Failed to sync {row['platform']}/{row['slug']}: {e}")

    success(f"Synced metrics for {synced} entries")


# ===== NEWSLETTER =====


@newsletter_app.command("serve")
def newsletter_serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
):
    """Start the newsletter signup API server."""
    import uvicorn

    info(f"Starting newsletter API on {host}:{port}")
    uvicorn.run(
        "myworkflow.newsletter.api:app",
        host=host,
        port=port,
        reload=False,
    )


@newsletter_app.command("subscribers")
def newsletter_subscribers(
    all_subs: bool = typer.Option(False, "--all", help="Include unsubscribed"),
):
    """List newsletter subscribers."""
    config = load_config()
    with get_db(config.db_path) as db:
        if all_subs:
            rows = db.execute(
                "SELECT * FROM subscribers ORDER BY subscribed_at DESC"
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM subscribers WHERE unsubscribed_at IS NULL ORDER BY subscribed_at DESC"
            ).fetchall()

    if not rows:
        info("No subscribers yet")
        return

    table = Table(title="Subscribers")
    table.add_column("Email")
    table.add_column("Status")
    table.add_column("Subscribed")

    for row in rows:
        if row["unsubscribed_at"]:
            status = "Unsubscribed"
        elif row["confirmed"]:
            status = "Confirmed"
        else:
            status = "Pending"
        table.add_row(row["email"], status, row["subscribed_at"])
    console.print(table)


@newsletter_app.command("send")
def newsletter_send(
    slug: str = typer.Argument(..., help="Edition slug"),
    subject: str = typer.Argument(..., help="Email subject"),
    content_path: Path = typer.Argument(..., help="Path to HTML content file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without sending"),
):
    """Send a newsletter edition to confirmed subscribers."""
    config = load_config()

    if not content_path.exists():
        error(f"File not found: {content_path}")
        raise typer.Exit(1)

    html_content = content_path.read_text()

    from myworkflow.newsletter.sender import render_edition, send_email

    with get_db(config.db_path) as db:
        subscribers = db.execute(
            "SELECT * FROM subscribers WHERE confirmed = 1 AND unsubscribed_at IS NULL"
        ).fetchall()

    if not subscribers:
        warn("No confirmed subscribers to send to")
        return

    info(f"Sending '{subject}' to {len(subscribers)} subscribers")

    if dry_run:
        info("Dry run -- no emails sent")
        for s in subscribers:
            console.print(f"  Would send to: {s['email']}")
        return

    if not config.resend_api_key:
        error("RESEND_API_KEY not set")
        raise typer.Exit(1)

    # Record edition
    with get_db(config.db_path) as db:
        db.execute(
            "INSERT INTO editions (slug, subject, html_body) VALUES (?, ?, ?)",
            (slug, subject, html_content),
        )
        edition_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    sent_count = 0
    for sub in subscribers:
        rendered = render_edition(
            "edition.html",
            subject=subject,
            content=html_content,
            unsubscribe_url=f"{config.blog_url}/api/unsubscribe?token={sub['unsubscribe_token']}",
        )
        try:
            result = send_email(
                api_key=config.resend_api_key,
                from_email=config.newsletter_from_email,
                to_email=sub["email"],
                subject=subject,
                html=rendered,
            )
            with get_db(config.db_path) as db:
                db.execute(
                    "INSERT INTO send_log (edition_id, subscriber_id, resend_id) VALUES (?, ?, ?)",
                    (edition_id, sub["id"], result.get("id", "")),
                )
            sent_count += 1
        except Exception as e:
            error(f"Failed to send to {sub['email']}: {e}")

    with get_db(config.db_path) as db:
        db.execute(
            "UPDATE editions SET sent_at = datetime('now'), recipient_count = ? WHERE id = ?",
            (sent_count, edition_id),
        )

    success(f"Sent to {sent_count}/{len(subscribers)} subscribers")


# ===== STATS =====


@app.command("stats")
def stats():
    """Quick summary of content pipeline status."""
    config = load_config()

    with get_db(config.db_path) as db:
        post_count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        queue_count = db.execute(
            "SELECT COUNT(*) FROM social_queue WHERE status IN ('queued', 'approved')"
        ).fetchone()[0]
        review_count = db.execute(
            "SELECT COUNT(*) FROM social_queue WHERE status = 'needs_review'"
        ).fetchone()[0]
        sub_count = db.execute(
            "SELECT COUNT(*) FROM subscribers WHERE confirmed = 1 AND unsubscribed_at IS NULL"
        ).fetchone()[0]
        edition_count = db.execute("SELECT COUNT(*) FROM editions").fetchone()[0]
        ledger_count = db.execute(
            "SELECT COUNT(*) FROM content_ledger WHERE status = 'posted'"
        ).fetchone()[0]

    table = Table(title="myworkflow stats")
    table.add_column("Metric")
    table.add_column("Count")
    table.add_row("Cross-posted articles", str(post_count))
    table.add_row("Queued social posts", str(queue_count))
    table.add_row("Awaiting review", str(review_count))
    table.add_row("Platform posts (ledger)", str(ledger_count))
    table.add_row("Confirmed subscribers", str(sub_count))
    table.add_row("Newsletter editions", str(edition_count))
    console.print(table)


@app.command("init")
def init_cmd():
    """Initialize the database and config directory."""
    config = load_config()
    init_db(config.db_path)
    success(f"Database initialized: {config.db_path}")
    success(f"Config dir: {config.config_dir}")


if __name__ == "__main__":
    app()
