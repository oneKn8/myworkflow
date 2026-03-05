"""Newsletter sending via Resend API."""

import resend
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )


def render_edition(
    template_name: str,
    subject: str,
    content: str,
    unsubscribe_url: str = "",
) -> str:
    """Render an email edition from template."""
    env = _get_jinja_env()
    template = env.get_template(template_name)
    return template.render(
        subject=subject,
        content=content,
        unsubscribe_url=unsubscribe_url,
    )


def send_email(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    html: str,
) -> dict:
    """Send a single email via Resend."""
    resend.api_key = api_key
    result = resend.Emails.send(
        {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
    )
    return {"id": result.get("id", "")}


def send_confirmation(
    api_key: str,
    from_email: str,
    to_email: str,
    confirm_url: str,
) -> dict:
    """Send double opt-in confirmation email."""
    env = _get_jinja_env()
    template = env.get_template("confirm.html")
    html = template.render(confirm_url=confirm_url)

    return send_email(
        api_key=api_key,
        from_email=from_email,
        to_email=to_email,
        subject="Confirm your subscription to Shifat Santo's newsletter",
        html=html,
    )
