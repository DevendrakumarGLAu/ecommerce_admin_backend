"""Custom, self-hosted CAPTCHA challenge for login — no external/paid service.

A short-lived challenge is generated server-side: a random alphanumeric
string rendered as a hand-built SVG (randomized per-character rotation,
position, color, plus a few noise lines/dots — enough to stop naive
scripted login attempts on a small internal app; not meant to withstand a
dedicated attacker running OCR).

Only the bcrypt hash of the answer is stored, keyed by a random `captcha_id`,
in the same Redis/in-memory cache used elsewhere (`app.core.redis`) with a
short TTL — no new database table needed for something this ephemeral. The
whole challenge is single-use: `verify()` deletes it immediately regardless
of whether the answer was right or wrong, so a captured challenge can never
be retried or brute-forced offline.
"""

import random
import secrets

from app.core.config import settings
from app.core.redis import cache_delete, cache_get, cache_set
from app.core.security import hash_password, verify_password
from app.utils.exceptions import BadRequestException

_CACHE_PREFIX = "captcha"
# Visually ambiguous characters (0/O, 1/l/I) are excluded since this is read off an image.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_WIDTH = 180
_HEIGHT = 60


def _cache_key(captcha_id: str) -> str:
    return f"{_CACHE_PREFIX}:{captcha_id}"


def _random_text() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(settings.CAPTCHA_LENGTH))


def _build_svg(text: str) -> str:
    """Hand-rolled distorted-text SVG. `random` (not `secrets`) is fine here —
    only the visual jitter is randomized, not the secret answer itself."""
    rng = random.Random()
    char_width = _WIDTH // len(text)

    noise_lines = "".join(
        f'<line x1="{rng.randint(0, _WIDTH)}" y1="{rng.randint(0, _HEIGHT)}" '
        f'x2="{rng.randint(0, _WIDTH)}" y2="{rng.randint(0, _HEIGHT)}" '
        f'stroke="#{rng.randint(150, 210):02x}{rng.randint(150, 210):02x}{rng.randint(150, 210):02x}" '
        f'stroke-width="1.5" />'
        for _ in range(6)
    )
    noise_dots = "".join(
        f'<circle cx="{rng.randint(0, _WIDTH)}" cy="{rng.randint(0, _HEIGHT)}" r="{rng.uniform(0.5, 1.5):.1f}" '
        f'fill="#{rng.randint(120, 180):02x}{rng.randint(120, 180):02x}{rng.randint(120, 180):02x}" />'
        for _ in range(25)
    )
    glyphs = "".join(
        f'<text x="{i * char_width + char_width / 2 + rng.randint(-4, 4)}" '
        f'y="{_HEIGHT / 2 + rng.randint(-6, 6)}" '
        f'transform="rotate({rng.randint(-25, 25)} {i * char_width + char_width / 2} {_HEIGHT / 2})" '
        f'font-family="Verdana, sans-serif" font-size="{rng.randint(26, 32)}" font-weight="bold" '
        f'fill="#{rng.randint(20, 90):02x}{rng.randint(20, 90):02x}{rng.randint(20, 90):02x}" '
        f'text-anchor="middle" dominant-baseline="middle">{char}</text>'
        for i, char in enumerate(text)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_WIDTH}" height="{_HEIGHT}" '
        f'viewBox="0 0 {_WIDTH} {_HEIGHT}">'
        f'<rect width="{_WIDTH}" height="{_HEIGHT}" fill="#f4f4f5" />'
        f"{noise_dots}{noise_lines}{glyphs}"
        f"</svg>"
    )


async def generate() -> tuple[str, str]:
    """Create a new challenge. Returns `(captcha_id, svg_markup)`."""
    text = _random_text()
    captcha_id = secrets.token_urlsafe(16)

    await cache_set(
        _cache_key(captcha_id),
        hash_password(text.lower()),
        ttl=settings.CAPTCHA_EXPIRY_MINUTES * 60,
    )

    return captcha_id, _build_svg(text)


async def verify(captcha_id: str, text: str) -> None:
    """Raises `BadRequestException` if the answer is wrong, missing, or expired.

    Single-use by design: the challenge is deleted the moment this runs,
    whether the answer turns out right or wrong.
    """
    key = _cache_key(captcha_id)
    stored_hash = await cache_get(key)
    await cache_delete(key)

    if stored_hash is None:
        raise BadRequestException("Captcha has expired. Please try again.")

    if not verify_password(text.strip().lower(), stored_hash):
        raise BadRequestException("Incorrect captcha. Please try again.")
