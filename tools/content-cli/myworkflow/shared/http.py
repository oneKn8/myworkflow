"""HTTP client with retry logic."""

import httpx
from typing import Any


def create_client(
    base_url: str = "",
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> httpx.Client:
    transport = httpx.HTTPTransport(retries=3)
    return httpx.Client(
        base_url=base_url,
        headers=headers or {},
        timeout=timeout,
        transport=transport,
    )


def post_json(
    client: httpx.Client,
    url: str,
    data: dict[str, Any],
) -> httpx.Response:
    resp = client.post(url, json=data)
    resp.raise_for_status()
    return resp
