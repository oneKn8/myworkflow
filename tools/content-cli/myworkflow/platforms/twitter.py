"""X (Twitter) posting via v2 API."""

from myworkflow.shared.http import create_client


TWITTER_API = "https://api.twitter.com/2"


def post_tweet(
    bearer_token: str,
    text: str,
    reply_to: str | None = None,
) -> dict:
    """Post a tweet. Returns tweet ID and URL."""
    client = create_client(
        base_url=TWITTER_API,
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        },
    )

    payload: dict = {"text": text}
    if reply_to:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to}

    resp = client.post("/tweets", json=payload)
    resp.raise_for_status()
    data = resp.json()["data"]
    return {
        "id": data["id"],
        "url": f"https://x.com/i/web/status/{data['id']}",
    }


def post_thread(bearer_token: str, tweets: list[str]) -> list[dict]:
    """Post a thread of tweets. Returns list of tweet data."""
    results = []
    reply_to = None
    for text in tweets:
        result = post_tweet(bearer_token, text, reply_to=reply_to)
        results.append(result)
        reply_to = result["id"]
    return results
