"""Sends email via Gmail's SMTP server using an App Password.

No third-party email API and no extra dependency — just the stdlib `smtplib`
talking to `smtp.gmail.com:587` over STARTTLS. `smtplib` is blocking, so the
actual send runs in a worker thread (`asyncio.to_thread`) rather than
blocking the event loop.

Setup (one-time, on the Gmail account that will send the OTPs):
1. Turn on 2-Step Verification: https://myaccount.google.com/security
2. Create an App Password: Google Account -> Security -> App passwords.
3. Put the Gmail address in `SMTP_USERNAME` and the 16-character App Password
   in `SMTP_APP_PASSWORD` (see `.env.example`).
"""

import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.services.email.base import EmailProvider
from app.utils.exceptions import AppException


class EmailNotConfiguredError(AppException):
    default_message = "Email delivery is not configured on the server"


class GmailSMTPProvider(EmailProvider):
    async def send(self, to: str, subject: str, body: str) -> None:
        if not settings.smtp_configured:
            raise EmailNotConfiguredError(
                "SMTP_USERNAME/SMTP_APP_PASSWORD are not set — cannot send email"
            )

        message = EmailMessage()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.smtp_from_address}>"
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await asyncio.to_thread(self._send_sync, message)

    @staticmethod
    def _send_sync(message: EmailMessage) -> None:
        # App passwords are sometimes copy-pasted with spaces (Google displays
        # them in 4-character groups) — strip those before authenticating.
        app_password = settings.SMTP_APP_PASSWORD.replace(" ", "")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USERNAME, app_password)
            smtp.send_message(message)
