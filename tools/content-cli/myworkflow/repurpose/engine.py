"""LLM-powered content repurposing engine."""

from pathlib import Path
from anthropic import Anthropic

from myworkflow.repurpose.prompts import PROMPTS


FORMATS = list(PROMPTS.keys())


def repurpose(
    api_key: str,
    title: str,
    body: str,
    format: str,
    blog_url: str = "",
) -> str:
    """Repurpose a blog post into a specific format using Claude."""
    if format not in PROMPTS:
        raise ValueError(f"Unknown format: {format}. Available: {', '.join(FORMATS)}")

    client = Anthropic(api_key=api_key)
    prompt_template = PROMPTS[format]
    prompt = prompt_template.format(title=title, body=body, blog_url=blog_url)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def repurpose_all(
    api_key: str,
    title: str,
    body: str,
    blog_url: str = "",
) -> dict[str, str]:
    """Repurpose into all available formats."""
    results = {}
    for fmt in FORMATS:
        results[fmt] = repurpose(api_key, title, body, fmt, blog_url)
    return results
