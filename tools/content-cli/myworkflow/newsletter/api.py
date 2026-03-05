"""Newsletter signup FastAPI app (serve subcommand)."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from itsdangerous import URLSafeTimedSerializer
import re

import secrets

from myworkflow.config import load_config
from myworkflow.db import get_db
from myworkflow.newsletter.sender import send_confirmation


app = FastAPI(title="Newsletter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shifatsanto.dev", "http://localhost:4321"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class SubscribeRequest(BaseModel):
    email: str


def _validate_email(email: str) -> str:
    """Basic email validation without external deps for EmailStr."""
    email = email.strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise ValueError("Invalid email")
    return email


@app.post("/subscribe")
async def subscribe(req: SubscribeRequest):
    config = load_config()
    try:
        email = _validate_email(req.email)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid email address")

    serializer = URLSafeTimedSerializer(config.newsletter_confirm_secret)
    token = serializer.dumps(email, salt="subscribe")

    with get_db(config.db_path) as db:
        existing = db.execute(
            "SELECT id, confirmed FROM subscribers WHERE email = ?", (email,)
        ).fetchone()

        if existing and existing["confirmed"]:
            return {"message": "Already subscribed"}

        if existing:
            db.execute(
                "UPDATE subscribers SET confirm_token = ? WHERE id = ?",
                (token, existing["id"]),
            )
        else:
            unsub_token = secrets.token_urlsafe(32)
            db.execute(
                "INSERT INTO subscribers (email, confirm_token, unsubscribe_token) VALUES (?, ?, ?)",
                (email, token, unsub_token),
            )

    confirm_url = f"{config.blog_url}/api/confirm?token={token}"

    if config.resend_api_key:
        send_confirmation(
            api_key=config.resend_api_key,
            from_email=config.newsletter_from_email,
            to_email=email,
            confirm_url=confirm_url,
        )

    return {"message": "Check your email to confirm your subscription"}


@app.get("/confirm")
async def confirm(token: str):
    config = load_config()
    serializer = URLSafeTimedSerializer(config.newsletter_confirm_secret)

    try:
        email = serializer.loads(token, salt="subscribe", max_age=86400)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    with get_db(config.db_path) as db:
        db.execute(
            """UPDATE subscribers
               SET confirmed = 1, confirmed_at = datetime('now'), confirm_token = NULL
               WHERE email = ? AND confirmed = 0""",
            (email,),
        )

    return {"message": "Subscription confirmed"}


@app.get("/unsubscribe")
async def unsubscribe(token: str):
    config = load_config()

    with get_db(config.db_path) as db:
        row = db.execute(
            "SELECT id FROM subscribers WHERE unsubscribe_token = ?", (token,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="Invalid unsubscribe token")

        db.execute(
            "UPDATE subscribers SET unsubscribed_at = datetime('now') WHERE id = ?",
            (row["id"],),
        )

    return {"message": "You have been unsubscribed"}


@app.get("/health")
async def health():
    return {"status": "ok"}
