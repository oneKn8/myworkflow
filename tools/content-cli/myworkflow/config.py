"""Configuration loading and paths."""

from dataclasses import dataclass, field
from pathlib import Path
import os


def _config_dir() -> Path:
    d = Path(os.environ.get("MYWORKFLOW_CONFIG_DIR", "~/.config/myworkflow")).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _db_path() -> Path:
    return _config_dir() / "myworkflow.db"


@dataclass
class Config:
    # Paths
    config_dir: Path = field(default_factory=_config_dir)
    db_path: Path = field(default_factory=_db_path)
    blog_content_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "BLOG_CONTENT_DIR",
                "~/personal/myworkflow/blog/src/data",
            )
        ).expanduser()
    )
    blog_url: str = field(
        default_factory=lambda: os.environ.get("BLOG_URL", "https://shifatsanto.dev")
    )

    # Cross-posting
    devto_api_key: str = field(
        default_factory=lambda: os.environ.get("DEVTO_API_KEY", "")
    )
    hashnode_api_key: str = field(
        default_factory=lambda: os.environ.get("HASHNODE_API_KEY", "")
    )
    hashnode_publication_id: str = field(
        default_factory=lambda: os.environ.get("HASHNODE_PUBLICATION_ID", "")
    )

    # AI
    anthropic_api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )

    # Newsletter
    resend_api_key: str = field(
        default_factory=lambda: os.environ.get("RESEND_API_KEY", "")
    )
    newsletter_from_email: str = field(
        default_factory=lambda: os.environ.get(
            "NEWSLETTER_FROM_EMAIL", "santo@shifatsanto.dev"
        )
    )
    newsletter_confirm_secret: str = field(
        default_factory=lambda: os.environ.get(
            "NEWSLETTER_CONFIRM_SECRET", "change-me"
        )
    )


def load_config() -> Config:
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
    return Config()
