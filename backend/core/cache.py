"""In-memory response cache with 5-minute TTL.

Uses a plain Python dict — no external dependencies.
This cache is in-memory only and resets on every server restart.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

_TTL_SECONDS = 300  # 5 minutes


def make_key(body: dict) -> str:
    """SHA-256 hash of the deterministically serialised request body."""
    raw = json.dumps(body, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


class ResponseCache:
    """Plain-dict cache that stores (timestamp, result) tuples and evicts on TTL."""

    _MAX_SIZE = 256

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, body: dict) -> Any | None:
        """Return cached result for *body*, or None if missing or older than 5 minutes."""
        key = make_key(body)
        entry = self._store.get(key)
        if entry is None:
            return None
        timestamp, result = entry
        if time.time() - timestamp > _TTL_SECONDS:
            del self._store[key]
            return None
        return result

    def set(self, body: dict, result: Any) -> None:
        """Store *result* under the hash of *body* with the current timestamp."""
        key = make_key(body)
        self._store[key] = (time.time(), result)
        if len(self._store) > self._MAX_SIZE:
            # Evict the oldest entry by timestamp
            oldest_key = min(self._store, key=lambda k: self._store[k][0])
            del self._store[oldest_key]

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


# Module-level singleton shared across all requests.
response_cache = ResponseCache()
