"""Tests for POST /api/reconcile/medication."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.reconcile import ReconcileResponse, SafetyStatus

_API_KEY = "test-key"

VALID_PAYLOAD = {
    "patient_context": {
        "age": 67,
        "conditions": ["Type 2 Diabetes", "Hypertension"],
        "recent_labs": {"eGFR": 45},
    },
    "sources": [
        {
            "system": "Hospital EHR",
            "medication": "Metformin 1000mg twice daily",
            "last_updated": "2024-10-15",
            "source_reliability": "high",
        },
        {
            "system": "Primary Care",
            "medication": "Metformin 500mg twice daily",
            "last_updated": "2025-01-20",
            "source_reliability": "high",
        },
    ],
}

MOCK_RESPONSE = ReconcileResponse(
    reconciled_medication="Metformin 500mg twice daily",
    confidence_score=0.88,
    reasoning="Primary care record is most recent.",
    recommended_actions=["Update Hospital EHR"],
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


def _post(client, json):
    return client.post(
        "/api/reconcile/medication",
        json=json,
        headers={"X-API-Key": _API_KEY},
    )


def test_reconcile_input_validation_missing_sources(client):
    resp = _post(client, {})
    assert resp.status_code in (400, 422)


def test_reconcile_input_validation_empty_sources(client):
    resp = _post(client, {"sources": []})
    assert resp.status_code in (400, 422)


@patch("api.routes.reconcile.llm_reconcile", new_callable=AsyncMock,
       return_value=MOCK_RESPONSE)
def test_reconcile_valid_request_returns_correct_shape(mock_llm, client):
    resp = _post(client, VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {
        "reconciled_medication",
        "confidence_score",
        "reasoning",
        "recommended_actions",
        "clinical_safety_check",
    }
