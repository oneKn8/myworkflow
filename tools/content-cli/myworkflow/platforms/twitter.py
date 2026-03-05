"""X (Twitter) posting via tweepy with OAuth 1.0a (required for free tier)."""

import tweepy


def _get_client(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
) -> tweepy.Client:
    return tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )


def post_tweet(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
    text: str,
    reply_to: str | None = None,
) -> dict:
    """Post a single tweet. Returns tweet ID and URL."""
    client = _get_client(consumer_key, consumer_secret, access_token, access_token_secret)

    kwargs: dict = {"text": text}
    if reply_to:
        kwargs["in_reply_to_tweet_id"] = reply_to

    resp = client.create_tweet(**kwargs)
    tweet_id = resp.data["id"]
    return {
        "id": str(tweet_id),
        "url": f"https://x.com/i/web/status/{tweet_id}",
    }


def post_thread(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
    tweets: list[str],
) -> list[dict]:
    """Post a thread of tweets. Returns list of tweet data."""
    results = []
    reply_to = None
    for text in tweets:
        result = post_tweet(
            consumer_key, consumer_secret, access_token, access_token_secret,
            text, reply_to=reply_to,
        )
        results.append(result)
        reply_to = result["id"]
    return results
