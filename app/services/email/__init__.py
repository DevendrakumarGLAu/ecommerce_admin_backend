"""Factory for the active email provider — the single line to change when
swapping Gmail SMTP for a different provider later."""

from functools import lru_cache

from app.services.email.base import EmailProvider
from app.services.email.gmail_smtp_provider import GmailSMTPProvider

__all__ = ["EmailProvider", "get_email_provider"]


@lru_cache
def get_email_provider() -> EmailProvider:
    return GmailSMTPProvider()
