"""Dev.to API cross-posting."""

from myworkflow.shared.http import create_client, post_json


DEVTO_API = "https://dev.to/api"


def publish_article(
    api_key: str,
    title: str,
    body_markdown: str,
    tags: list[str],
    canonical_url: str,
    published: bool = True,
) -> dict:
    """Publish or create a draft article on Dev.to."""
    client = create_client(
        base_url=DEVTO_API,
        headers={"api-key": api_key, "Content-Type": "application/json"},
    )

    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "tags": tags[:4],  # Dev.to max 4 tags
            "canonical_url": canonical_url,
            "published": published,
        }
    }

    resp = post_json(client, "/articles", payload)
    data = resp.json()
    return {
        "id": data["id"],
        "url": data["url"],
        "slug": data["slug"],
    }


def get_article_stats(api_key: str, article_id: int) -> dict:
    """Get stats for a published article."""
    client = create_client(
        base_url=DEVTO_API,
        headers={"api-key": api_key},
    )
    resp = client.get(f"/articles/{article_id}")
    resp.raise_for_status()
    data = resp.json()
    return {
        "views": data.get("page_views_count", 0),
        "reactions": data.get("positive_reactions_count", 0),
        "comments": data.get("comments_count", 0),
    }
