"""myworkflow CLI -- unified content automation."""

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

app.add_typer(cross_post_app, name="cross-post")
app.add_typer(social_app, name="social")
app.add_typer(newsletter_app, name="newsletter")
app.add_typer(repurpose_app, name="repurpose")


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

    results = {}

    if platform in ("all", "devto"):
        if not config.devto_api_key:
            error("DEVTO_API_KEY not set")
        else:
            from myworkflow.platforms.devto import publish_article

            sanitized = sanitize_for_devto(body, canonical)
            result = publish_article(
                api_key=config.devto_api_key,
                title=title,
                body_markdown=sanitized,
                tags=tags,
                canonical_url=canonical,
            )
            results["devto"] = result
            success(f"Dev.to: {result['url']}")

    if platform in ("all", "hashnode"):
        if not config.hashnode_api_key or not config.hashnode_publication_id:
            error("HASHNODE_API_KEY or HASHNODE_PUBLICATION_ID not set")
        else:
            from myworkflow.platforms.hashnode import publish_article

            sanitized = sanitize_for_hashnode(body, canonical)
            result = publish_article(
                api_key=config.hashnode_api_key,
                publication_id=config.hashnode_publication_id,
                title=title,
                body_markdown=sanitized,
                tags=tags,
                canonical_url=canonical,
            )
            results["hashnode"] = result
            success(f"Hashnode: {result['url']}")

    # Track in DB
    with get_db(config.db_path) as db:
        db.execute(
            """INSERT OR REPLACE INTO posts (slug, title, local_path, devto_url, devto_id, hashnode_url, hashnode_id, canonical_url, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
        console.print(f"\n[bold cyan]--- {fmt.upper()} ---[/bold cyan]")
        console.print(content)

        if output:
            output.mkdir(parents=True, exist_ok=True)
            (output / f"{slug}-{fmt}.txt").write_text(content)
            info(f"Saved: {output / f'{slug}-{fmt}.txt'}")

        if enqueue and fmt in ("twitter", "linkedin", "reddit"):
            with get_db(config.db_path) as db:
                db.execute(
                    """INSERT INTO social_queue (post_slug, platform, content, scheduled_at, status)
                       VALUES (?, ?, ?, ?, 'queued')""",
                    (slug, fmt, content, at),
                )
            success(f"Enqueued {fmt} post" + (f" for {at}" if at else ""))


# ===== SOCIAL =====


@social_app.command("list")
def social_list():
    """List queued social posts."""
    config = load_config()
    with get_db(config.db_path) as db:
        rows = db.execute(
            "SELECT * FROM social_queue ORDER BY created_at DESC LIMIT 20"
        ).fetchall()

    if not rows:
        info("No queued posts")
        return

    table = Table(title="Social Queue")
    table.add_column("ID")
    table.add_column("Slug")
    table.add_column("Platform")
    table.add_column("Status")
    table.add_column("Scheduled")
    table.add_column("Content", max_width=40)

    for row in rows:
        table.add_row(
            str(row["id"]),
            row["post_slug"],
            row["platform"],
            row["status"],
            row["scheduled_at"] or "now",
            row["content"][:40] + "...",
        )
    console.print(table)


@social_app.command("enqueue")
def social_enqueue(
    slug: str = typer.Argument(..., help="Post slug"),
    platform: str = typer.Argument(..., help="Platform: twitter, linkedin, reddit"),
    content: str = typer.Argument(..., help="Post content"),
    at: Optional[str] = typer.Option(None, "--at", help="Schedule time"),
):
    """Manually enqueue a social post."""
    config = load_config()
    with get_db(config.db_path) as db:
        db.execute(
            """INSERT INTO social_queue (post_slug, platform, content, scheduled_at, status)
               VALUES (?, ?, ?, ?, 'queued')""",
            (slug, platform, content, at),
        )
    success(f"Enqueued {platform} post for {slug}")


@social_app.command("drain")
def social_drain():
    """Process and post all queued (and due) social posts."""
    config = load_config()
    now = datetime.now().isoformat()

    with get_db(config.db_path) as db:
        rows = db.execute(
            """SELECT * FROM social_queue
               WHERE status = 'queued'
               AND (scheduled_at IS NULL OR scheduled_at <= ?)
               ORDER BY created_at""",
            (now,),
        ).fetchall()

    if not rows:
        info("Nothing to drain")
        return

    for row in rows:
        platform = row["platform"]
        content = row["content"]
        post_id = row["id"]

        info(f"Posting to {platform}...")

        try:
            post_url = _post_to_platform(config, platform, content, row["post_slug"])
            with get_db(config.db_path) as db:
                db.execute(
                    """UPDATE social_queue
                       SET status = 'posted', posted_at = datetime('now'), post_url = ?
                       WHERE id = ?""",
                    (post_url, post_id),
                )
            success(f"Posted to {platform}: {post_url}")
        except Exception as e:
            with get_db(config.db_path) as db:
                db.execute(
                    """UPDATE social_queue
                       SET status = 'failed', error_message = ?
                       WHERE id = ?""",
                    (str(e), post_id),
                )
            error(f"Failed {platform}: {e}")


def _post_to_platform(config, platform: str, content: str, slug: str) -> str:
    """Dispatch to the appropriate platform API."""
    blog_url = f"{config.blog_url}/blog/{slug}"

    if platform == "twitter":
        from myworkflow.platforms.twitter import post_tweet

        # For threads, split on ---
        tweets = [t.strip() for t in content.split("---") if t.strip()]
        if len(tweets) > 1:
            from myworkflow.platforms.twitter import post_thread

            results = post_thread("", tweets)  # TODO: OAuth token management
            return results[-1]["url"]
        else:
            result = post_tweet("", tweets[0])
            return result["url"]

    elif platform == "linkedin":
        from myworkflow.platforms.linkedin import post_article

        result = post_article("", "", content, blog_url)
        return f"https://linkedin.com/feed/update/{result['id']}"

    elif platform == "reddit":
        # Parse TITLE and BODY from formatted content
        return ""  # TODO: implement with subreddit config

    else:
        raise ValueError(f"Unknown platform: {platform}")


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
def newsletter_subscribers():
    """List newsletter subscribers."""
    config = load_config()
    with get_db(config.db_path) as db:
        rows = db.execute(
            "SELECT * FROM subscribers ORDER BY subscribed_at DESC"
        ).fetchall()

    if not rows:
        info("No subscribers yet")
        return

    table = Table(title="Subscribers")
    table.add_column("Email")
    table.add_column("Confirmed")
    table.add_column("Subscribed")

    for row in rows:
        table.add_row(
            row["email"],
            "Yes" if row["confirmed"] else "No",
            row["subscribed_at"],
        )
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
            "SELECT COUNT(*) FROM social_queue WHERE status = 'queued'"
        ).fetchone()[0]
        sub_count = db.execute(
            "SELECT COUNT(*) FROM subscribers WHERE confirmed = 1"
        ).fetchone()[0]
        edition_count = db.execute("SELECT COUNT(*) FROM editions").fetchone()[0]

    table = Table(title="myworkflow stats")
    table.add_column("Metric")
    table.add_column("Count")
    table.add_row("Cross-posted articles", str(post_count))
    table.add_row("Queued social posts", str(queue_count))
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
