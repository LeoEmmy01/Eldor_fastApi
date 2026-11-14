import logging
import os
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def _is_production() -> bool:
    env = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
    return env in {"production", "prod"}


def send_password_reset_email(to_email: str, token: str) -> None:
    """Email a password reset link. Never raises, so failures can't leak account existence."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?{urlencode({'token': token, 'email': to_email})}"

    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        if _is_production():
            # Never log the token/link in production
            logger.error("SMTP_HOST is not configured; password reset email was not sent.")
        else:
            logger.info("[DEV ONLY] Password reset link for %s: %s", to_email, reset_link)
        return

    msg = EmailMessage()
    msg["Subject"] = "Reset your password"
    msg["From"] = os.getenv("EMAIL_FROM", "no-reply@example.com")
    msg["To"] = to_email
    msg.set_content(
        "We received a request to reset your password.\n\n"
        f"Use this link within 15 minutes:\n{reset_link}\n\n"
        "If you didn't request this, you can ignore this email."
    )

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(smtp_host, port, timeout=10) as server:
            server.starttls()
            user, password = os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD")
            if user and password:
                server.login(user, password)
            server.send_message(msg)
    except Exception:
        logger.exception("Failed to send password reset email.")