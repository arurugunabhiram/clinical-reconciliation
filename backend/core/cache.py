"""Simple in-memory LRU cache for reconciliation results."""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any

_DEFAULT_MAX = 256


class LRUCache:
    def __init__(self, max_size: int = _DEFAULT_MAX) -> None:
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max = max_size

    @staticmethod
    def _make_key(data: dict) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, data: dict) -> Any | None:
        key = self._make_key(data)
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def set(self, data: dict, value: Any) -> None:
        key = self._make_key(data)
        self._store[key] = value
        self._store.move_to_end(key)
        if len(self._store) > self._max:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


reconcile_cache = LRUCache()
