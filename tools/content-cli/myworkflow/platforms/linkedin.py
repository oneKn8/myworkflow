"""LinkedIn posting via v2 API."""

from myworkflow.shared.http import create_client


LINKEDIN_API = "https://api.linkedin.com/v2"


def post_article(
    access_token: str,
    author_urn: str,
    text: str,
    article_url: str | None = None,
    article_title: str | None = None,
) -> dict:
    """Create a LinkedIn post, optionally with article link."""
    client = create_client(
        base_url=LINKEDIN_API,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
    )

    payload: dict = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    if article_url:
        media_content = payload["specificContent"]["com.linkedin.ugc.ShareContent"]
        media_content["shareMediaCategory"] = "ARTICLE"
        media_content["media"] = [
            {
                "status": "READY",
                "originalUrl": article_url,
                **({"title": {"text": article_title}} if article_title else {}),
            }
        ]

    resp = client.post("/ugcPosts", json=payload)
    resp.raise_for_status()
    return {"id": resp.headers.get("x-restli-id", "")}
