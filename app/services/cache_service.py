"""Cache key conventions and invalidation helpers for cached listings.

Product/category listings are cached per unique query string so different
filter/sort/page combinations don't collide. Any write to the underlying
table invalidates the whole prefix rather than trying to selectively patch
individual cached pages.
"""

from typing import Any

from app.core.redis import cache_delete, cache_delete_pattern, cache_get, cache_set

PRODUCTS_LIST_PREFIX = "cache:products:list"
CATEGORIES_LIST_PREFIX = "cache:categories:list"
SETTINGS_KEY = "cache:settings"


def build_products_list_key(query_string: str) -> str:
    return f"{PRODUCTS_LIST_PREFIX}:{query_string}"


def build_categories_list_key(query_string: str) -> str:
    return f"{CATEGORIES_LIST_PREFIX}:{query_string}"


async def get_cached(key: str) -> Any | None:
    return await cache_get(key)


async def set_cached(key: str, value: Any, ttl: int | None = None) -> None:
    await cache_set(key, value, ttl)


async def invalidate_products_cache() -> None:
    await cache_delete_pattern(f"{PRODUCTS_LIST_PREFIX}:*")


async def invalidate_categories_cache() -> None:
    await cache_delete_pattern(f"{CATEGORIES_LIST_PREFIX}:*")


async def invalidate_settings_cache() -> None:
    await cache_delete(SETTINGS_KEY)
