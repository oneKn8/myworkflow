"""LinkedIn posting via Posts API (v202402+)."""

from myworkflow.shared.http import create_client


LINKEDIN_API = "https://api.linkedin.com/rest"


def post_update(
    access_token: str,
    person_id: str,
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
            "LinkedIn-Version": "202402",
        },
    )

    payload: dict = {
        "author": f"urn:li:person:{person_id}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
    }

    if article_url:
        payload["content"] = {
            "article": {
                "source": article_url,
                **({"title": article_title} if article_title else {}),
            }
        }

    resp = client.post("/posts", json=payload)
    resp.raise_for_status()
    post_id = resp.headers.get("x-restli-id", "")
    return {
        "id": post_id,
        "url": f"https://www.linkedin.com/feed/update/{post_id}",
    }
