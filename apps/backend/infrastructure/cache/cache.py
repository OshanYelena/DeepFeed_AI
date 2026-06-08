"""
DeepFeed AI - Application Cache (M18 Performance Optimization)
In-memory TTL cache for feed results and topic preferences.
Reduces DB load on repeated requests.
Swap with Redis in production (TDS §18 Performance Optimization).
"""
import time
from typing import Any, Optional
from dataclasses import dataclass, field
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    value: Any
    expires_at: float

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class TTLCache:
    """Simple in-memory TTL cache. Thread-safe for single process."""

    def __init__(self, default_ttl: int = 300) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self._default_ttl
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> int:
        """Delete all keys starting with prefix. Returns count deleted."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def clear(self) -> None:
        self._store.clear()

    def evict_expired(self) -> int:
        """Remove expired entries. Returns count evicted."""
        now = time.time()
        expired = [k for k, v in self._store.items() if v.expires_at < now]
        for k in expired:
            del self._store[k]
        return len(expired)

    @property
    def size(self) -> int:
        return len(self._store)


# ── Cache Instances ────────────────────────────────────────────────────────────

# Feed cache: 5 minutes (feeds change after ranking runs)
feed_cache = TTLCache(default_ttl=300)

# Topic preferences cache: 15 minutes
preferences_cache = TTLCache(default_ttl=900)

# Source list cache: 30 minutes (rarely changes)
source_cache = TTLCache(default_ttl=1800)

# Summary cache: 24 hours (summaries are stable once generated)
summary_cache = TTLCache(default_ttl=86400)


def feed_cache_key(user_id: str, limit: int, offset: int, content_type: str = "", min_score: float = 0.0) -> str:
    return f"feed:{user_id}:{limit}:{offset}:{content_type}:{min_score}"


def prefs_cache_key(user_id: str) -> str:
    return f"prefs:{user_id}"


def invalidate_user_feed(user_id: str) -> None:
    """Call this when recommendations are updated for a user."""
    count = feed_cache.delete_prefix(f"feed:{user_id}:")
    logger.info("feed_cache_invalidated", user_id=user_id, keys_cleared=count)


def invalidate_user_prefs(user_id: str) -> None:
    """Call this when user preferences are updated."""
    preferences_cache.delete(prefs_cache_key(user_id))
    logger.info("prefs_cache_invalidated", user_id=user_id)
