"""Tests for X-API-Key authentication."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.reconcile import ReconcileResponse, SafetyStatus

_API_KEY = "test-key"

VALID_PAYLOAD = {
    "sources": [
        {
            "system": "Hospital EHR",
            "medication": "Metformin 500mg twice daily",
            "source_reliability": "high",
        }
    ]
}

MOCK_RESPONSE = ReconcileResponse(
    reconciled_medication="Metformin 500mg twice daily",
    confidence_score=0.9,
    reasoning="Single source.",
    recommended_actions=[],
    clinical_safety_check=SafetyStatus.PASSED,
)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("API_KEY", _API_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")


@pytest.fixture(autouse=True)
def _clear_cache():
    from core.cache import response_cache
    response_cache.clear()
    yield
    response_cache.clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_missing_api_key_returns_401(client):
    resp = client.post("/api/reconcile/medication", json=VALID_PAYLOAD)
    assert resp.status_code == 401
    assert resp.json() == {"error": "Unauthorized", "message": "Valid X-API-Key header required"}


def test_wrong_api_key_returns_401(client):
    resp = client.post(
        "/api/reconcile/medication",
        json=VALID_PAYLOAD,
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "Unauthorized"


@patch("api.routes.reconcile.llm_reconcile", new_callable=AsyncMock,
       return_value=MOCK_RESPONSE)
def test_correct_api_key_passes(mock_llm, client):
    resp = client.post(
        "/api/reconcile/medication",
        json=VALID_PAYLOAD,
        headers={"X-API-Key": _API_KEY},
    )
    assert resp.status_code != 401
