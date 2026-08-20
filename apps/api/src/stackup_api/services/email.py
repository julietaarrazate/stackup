"""Transactional email via Resend.

Gated on RESEND_API_KEY: when unset (dev/test), emails are logged instead of
sent, so flows are testable without an email provider. Sending is a single
HTTPS call to Resend's API.
"""

from __future__ import annotations

import httpx

from stackup_api.core.config import get_settings
from stackup_api.core.logging import get_logger

logger = get_logger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"


async def send_email(*, to: str, subject: str, html: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        logger.info("email.skipped_no_provider", to=to, subject=subject)
        return
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            _RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.email_from,
                "to": [to],
                "subject": subject,
                "html": html,
            },
        )
    if resp.status_code >= 400:
        logger.error("email.send_failed", to=to, status=resp.status_code)
        raise RuntimeError(f"Email send failed with status {resp.status_code}")
    logger.info("email.sent", to=to, subject=subject)


def password_reset_email(token: str) -> tuple[str, str]:
    """(subject, html) for a password-reset email."""
    base = get_settings().frontend_link_base
    link = f"{base}/reset-password?token={token}"
    subject = "Restablecé tu contraseña de STACKUP"
    html = (
        "<p>Recibimos un pedido para restablecer tu contraseña.</p>"
        f'<p><a href="{link}">Restablecer contraseña</a></p>'
        "<p>Si no fuiste vos, ignorá este mensaje. El enlace vence pronto.</p>"
    )
    return subject, html


def verify_email(token: str) -> tuple[str, str]:
    """(subject, html) for an email-verification email."""
    base = get_settings().frontend_link_base
    link = f"{base}/verify?token={token}"
    subject = "Verificá tu email en STACKUP"
    html = (
        f'<p>¡Bienvenido a STACKUP!</p><p><a href="{link}">Verificar mi email</a></p>'
    )
    return subject, html
