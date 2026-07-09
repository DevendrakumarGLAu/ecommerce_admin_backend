"""Redis client and generic cache helpers used across the application.

At initial/dev stage there's no real Redis instance available, so
`settings.USE_REDIS=False` (the default) routes everything through an
in-process `InMemoryRedis` that implements the handful of methods the
rest of the app actually calls (get/set/delete/incr/expire/scan). This
means token blacklisting, rate limiting, and listing caches all work
with zero external dependencies — the tradeoff is that state resets on
every process restart and isn't shared across multiple workers.

Flip `USE_REDIS=true` in `.env` (with a real `REDIS_URL`) once Redis is
provisioned; every call site below is unchanged either way.
"""

import asyncio
import fnmatch
import json
import time
from typing import Any

from app.core.config import settings


class InMemoryRedis:
    """Minimal async in-memory stand-in for the subset of the Redis API this app uses."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    def _expired(self, key: str) -> bool:
        entry = self._store.get(key)
        if entry is None:
            return True
        _, expires_at = entry
        return expires_at is not None and expires_at <= time.monotonic()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if self._expired(key):
                self._store.pop(key, None)
                return None
            return self._store[key][0]

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        async with self._lock:
            expires_at = time.monotonic() + ex if ex else None
            self._store[key] = (value, expires_at)

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            removed = 0
            for key in keys:
                if self._store.pop(key, None) is not None:
                    removed += 1
            return removed

    async def incr(self, key: str) -> int:
        async with self._lock:
            if self._expired(key):
                self._store.pop(key, None)
            value, expires_at = self._store.get(key, (0, None))
            new_value = int(value) + 1
            self._store[key] = (new_value, expires_at)
            return new_value

    async def expire(self, key: str, seconds: int) -> None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is not None:
                self._store[key] = (entry[0], time.monotonic() + seconds)

    async def scan(self, cursor: int = 0, match: str = "*", count: int = 100) -> tuple[int, list[str]]:
        async with self._lock:
            keys = [k for k in self._store if not self._expired(k) and fnmatch.fnmatch(k, match)]
            return 0, keys

    async def aclose(self) -> None:
        async with self._lock:
            self._store.clear()


def _build_client() -> Any:
    if not settings.USE_REDIS:
        return InMemoryRedis()

    from redis.asyncio import ConnectionPool, Redis

    pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
    return Redis(connection_pool=pool)


redis_client: Any = _build_client()


async def close_redis() -> None:
    """Close the Redis connection (or clear the in-memory store) on application shutdown."""
    await redis_client.aclose()


async def cache_get(key: str) -> Any | None:
    """Fetch and JSON-decode a cached value, returning None on miss/error."""
    raw = await redis_client.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """JSON-encode and store a value with an optional TTL (seconds)."""
    payload = json.dumps(value, default=str)
    await redis_client.set(key, payload, ex=ttl or settings.CACHE_TTL_SECONDS)


async def cache_delete(*keys: str) -> None:
    """Delete one or more explicit cache keys."""
    if keys:
        await redis_client.delete(*keys)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern (used for bulk cache invalidation)."""
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break
