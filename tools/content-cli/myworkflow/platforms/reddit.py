"""Reddit posting via API."""

from myworkflow.shared.http import create_client


REDDIT_API = "https://oauth.reddit.com"
REDDIT_AUTH = "https://www.reddit.com/api/v1/access_token"


def get_access_token(
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> str:
    """Get Reddit OAuth2 access token."""
    client = create_client()
    resp = client.post(
        REDDIT_AUTH,
        auth=(client_id, client_secret),
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        headers={"User-Agent": "myworkflow/0.1.0"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def submit_link(
    access_token: str,
    subreddit: str,
    title: str,
    url: str,
) -> dict:
    """Submit a link post to a subreddit."""
    client = create_client(
        base_url=REDDIT_API,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "myworkflow/0.1.0",
        },
    )

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
