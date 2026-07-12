"""OTP delivery — the one seam `PasswordResetService` depends on.

Delivery goes through whatever `app.services.email.get_email_provider()`
returns (Gmail SMTP today). To move off Gmail later, add a new
`EmailProvider` implementation and change `get_email_provider()` — nothing
here or in `PasswordResetService` needs to change.

A delivery failure (bad Gmail credentials, network hiccup, etc.) is logged
but does not raise: the OTP is already safely stored server-side by the time
this runs, so a transient email failure shouldn't turn into a 500 for the
user. `settings.OTP_DEBUG_MODE` — independent of whether email is even
configured — is the escape hatch for testing without a working Gmail App
Password on hand.
"""

from app.core.logging import get_logger
from app.models.user import User
from app.services.email import get_email_provider

logger = get_logger("app.otp_notifier")

_SUBJECT = "Your password reset code"


def _build_body(otp: str, expiry_minutes: int) -> str:
    return (
        f"Your password reset code is: {otp}\n\n"
        f"This code expires in {expiry_minutes} minutes and can only be used once.\n\n"
        "If you didn't request this, you can safely ignore this email."
    )


async def send_otp(user: User, otp: str, expiry_minutes: int) -> None:
    """Deliver a password-reset OTP to the user's registered email."""
    logger.info("Password-reset OTP generated", extra={"user_id": str(user.id), "email": user.email})

    try:
        await get_email_provider().send(
            to=user.email,
            subject=_SUBJECT,
            body=_build_body(otp, expiry_minutes),
        )
        logger.info("Password-reset OTP email sent", extra={"user_id": str(user.id), "email": user.email})
    except Exception:
        logger.exception(
            "Failed to send password-reset OTP email — OTP is still valid server-side",
            extra={"user_id": str(user.id), "email": user.email},
        )
