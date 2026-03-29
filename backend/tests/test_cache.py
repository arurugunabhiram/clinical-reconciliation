"""Tests for the in-memory response cache."""

from __future__ import annotations

import time

import pytest

from core.cache import ResponseCache, make_key


@pytest.fixture()
def cache():
    c = ResponseCache()
    yield c
    c.clear()


def test_cache_hit_returns_cached_result(cache):
    body = {"sources": [{"system": "EHR", "medication": "Aspirin 81mg"}]}
    cache.set(body, "my-result")
    assert cache.get(body) == "my-result"


def test_cache_miss_after_ttl(cache, monkeypatch):
    body = {"key": "value"}
    cache.set(body, "stale-result")

    # Advance time past the 5-minute TTL
    original_time = time.time()
    monkeypatch.setattr("core.cache.time.time", lambda: original_time + 301)

    assert cache.get(body) is None


def test_cache_miss_on_unknown_key(cache):
    assert cache.get({"never": "stored"}) is None


def test_cache_key_is_deterministic():
    body = {"b": 2, "a": 1}
    key1 = make_key(body)
    key2 = make_key(body)
    assert key1 == key2


def test_cache_key_is_order_independent():
    assert make_key({"a": 1, "b": 2}) == make_key({"b": 2, "a": 1})


def test_cache_clear_removes_all_entries(cache):
    cache.set({"x": 1}, "v1")
    cache.set({"x": 2}, "v2")
    cache.clear()
    assert len(cache) == 0
