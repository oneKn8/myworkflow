"""HTTP client with retry logic. Never logs auth headers or payloads."""

import httpx
import logging
from typing import Any

# Suppress httpx debug logging that could leak tokens
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


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
