"""The one interface every email provider implements.

`otp_notifier.py` (and anything else that ever needs to email a user) depends
only on this — never on a concrete provider — so swapping Gmail SMTP for
SendGrid, SES, Postmark, etc. later means adding a new class here and
changing `get_email_provider()` in `__init__.py`. Nothing else moves.
"""

from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """Sends a single plain-text email. Implementations should raise on failure —
    callers decide whether a delivery failure should break the request or just
    be logged (see `otp_notifier.send_otp`)."""

    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...
