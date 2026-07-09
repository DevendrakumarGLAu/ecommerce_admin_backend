"""Pure slug-generation helpers (no database access)."""

from slugify import slugify as _slugify


def generate_slug(text: str) -> str:
    """Generate a URL-safe, lowercase, hyphenated slug from arbitrary text."""
    return _slugify(text)


def build_candidate_slug(base_slug: str, attempt: int) -> str:
    """Append a numeric suffix to a base slug for collision resolution.

    attempt=0 returns the base slug unchanged; attempt>=1 returns "base-N+1".
    """
    if attempt <= 0:
        return base_slug
    return f"{base_slug}-{attempt + 1}"
