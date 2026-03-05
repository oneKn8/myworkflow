"""Tests for UTM tag injection."""

from myworkflow.shared.utm import add_utm, inject_utm_into_content


def test_add_utm_basic():
    url = "https://shifatsanto.dev/blog/my-post"
    result = add_utm(url, source="twitter", slug="my-post")
    assert "utm_source=twitter" in result
    assert "utm_medium=social" in result
    assert "utm_campaign=my-post" in result


def test_add_utm_preserves_existing_params():
    url = "https://shifatsanto.dev/blog/my-post?ref=home"
    result = add_utm(url, source="linkedin", slug="my-post")
    assert "ref=home" in result
    assert "utm_source=linkedin" in result


def test_add_utm_no_overwrite():
    url = "https://shifatsanto.dev/blog/my-post?utm_source=existing"
    result = add_utm(url, source="twitter", slug="my-post")
    assert "utm_source=existing" in result
    assert "utm_source=twitter" not in result


def test_inject_utm_into_content():
    content = "Check out my post at https://shifatsanto.dev/blog/my-post for more."
    blog_url = "https://shifatsanto.dev/blog/my-post"
    result = inject_utm_into_content(content, blog_url, platform="reddit", slug="my-post")
    assert "utm_source=reddit" in result
    assert "utm_medium=social" in result
    assert "utm_campaign=my-post" in result
    assert "Check out my post at" in result
