"""MDX/markdown sanitization for cross-posting platforms."""

import re
from pathlib import Path
import frontmatter


def load_post(path: Path) -> tuple[dict, str]:
    """Load a markdown/MDX file, return (frontmatter_dict, body)."""
    post = frontmatter.load(path)
    return dict(post.metadata), post.content


def sanitize_for_devto(body: str, canonical_url: str) -> str:
    """Convert MDX body to Dev.to compatible markdown."""
    text = _strip_mdx_components(body)
    text = _strip_imports(text)
    text = _convert_callouts(text)
    return text


def sanitize_for_hashnode(body: str, canonical_url: str) -> str:
    """Convert MDX body to Hashnode compatible markdown."""
    text = _strip_mdx_components(body)
    text = _strip_imports(text)
    text = _convert_callouts(text)
    return text


def _strip_imports(text: str) -> str:
    """Remove ESM import statements."""
    return re.sub(r'^import\s+.*$', '', text, flags=re.MULTILINE)


def _strip_mdx_components(text: str) -> str:
    """Remove JSX/MDX component tags, keep their children."""
    # Self-closing components like <Component />
    text = re.sub(r'<\w+[^>]*/>', '', text)
    # Opening/closing tags -- keep inner content
    text = re.sub(r'<(\w+)[^>]*>(.*?)</\1>', r'\2', text, flags=re.DOTALL)
    return text


def _convert_callouts(text: str) -> str:
    """Convert custom callout syntax to blockquotes."""
    # :::note ... ::: -> > **Note:** ...
    def replace_callout(match: re.Match) -> str:
        kind = match.group(1).capitalize()
        content = match.group(2).strip()
        lines = content.split('\n')
        quoted = '\n'.join(f'> {line}' for line in lines)
        return f'> **{kind}:** {quoted.lstrip("> ")}'

    return re.sub(
        r':::(\w+)\n(.*?)\n:::', replace_callout, text, flags=re.DOTALL
    )
