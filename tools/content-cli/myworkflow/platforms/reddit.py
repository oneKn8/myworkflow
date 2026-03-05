"""Reddit posting via OAuth2 API."""

from myworkflow.shared.http import create_client


REDDIT_API = "https://oauth.reddit.com"
REDDIT_AUTH = "https://www.reddit.com/api/v1/access_token"
USER_AGENT = "myworkflow/0.1.0"


def get_access_token(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> str:
    """Get Reddit OAuth2 access token via password grant."""
    client = create_client()
    resp = client.post(
        REDDIT_AUTH,
        auth=(client_id, client_secret),
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        headers={"User-Agent": USER_AGENT},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _authed_client(access_token: str):
    return create_client(
        base_url=REDDIT_API,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
        },
    )


def submit_selftext(
    access_token: str,
    subreddit: str,
    title: str,
    body: str,
) -> dict:
    """Submit a self/text post to a subreddit."""
    client = _authed_client(access_token)
    resp = client.post(
        "/api/submit",
        data={
            "sr": subreddit,
            "kind": "self",
            "title": title,
            "text": body,
            "resubmit": "true",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return {"url": data.get("json", {}).get("data", {}).get("url", "")}


def submit_link(
    access_token: str,
    subreddit: str,
    title: str,
    url: str,
) -> dict:
    """Submit a link post to a subreddit."""
    client = _authed_client(access_token)
    resp = client.post(
        "/api/submit",
        data={
            "sr": subreddit,
            "kind": "link",
            "title": title,
            "url": url,
            "resubmit": "true",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return {"url": data.get("json", {}).get("data", {}).get("url", "")}
