"""UTM tag injection for outbound links."""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qs


def add_utm(url: str, source: str, slug: str) -> str:
    """Append UTM params to a URL. Preserves existing query params."""
    parsed = urlparse(url)
    existing = parse_qs(parsed.query)

    utm = {
        "utm_source": source,
        "utm_medium": "social",
        "utm_campaign": slug,
    }

    # Don't overwrite existing UTM params
    for key, val in utm.items():
        if key not in existing:
            existing[key] = [val]

    # Flatten single-value lists for clean URLs
    flat = {k: v[0] if len(v) == 1 else v for k, v in existing.items()}

    new_query = urlencode(flat, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def inject_utm_into_content(content: str, blog_url: str, platform: str, slug: str) -> str:
    """Replace bare blog_url occurrences in content with UTM-tagged version."""
    tagged = add_utm(blog_url, source=platform, slug=slug)
    return content.replace(blog_url, tagged)
