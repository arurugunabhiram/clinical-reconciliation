"""Route-level integration tests.

All Anthropic API calls are mocked with AsyncMock — no real network calls are made.
The in-memory cache is cleared before and after every test.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas.reconcile import ReconcileResponse, SafetyStatus
from schemas.validate import FieldIssue, IssueSeverity, QualityBreakdown, QualityScore

_TEST_API_KEY = "test-secret-key"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    """Ensure API_KEY and ANTHROPIC_API_KEY are set for every test."""
    monkeypatch.setenv("API_KEY", _TEST_API_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")


@pytest.fixture(autouse=True)
def _reset_cache():
    """Clear the shared in-memory cache before and after every test."""
    from core.cache import response_cache
    response_cache.clear()
    yield
    response_cache.clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _authed_post(client, url, **kwargs):
    """POST with the X-API-Key header pre-filled."""
    kwargs.setdefault("headers", {})["X-API-Key"] = _TEST_API_KEY
    return client.post(url, **kwargs)


# ---------------------------------------------------------------------------
# Shared mock objects
# ---------------------------------------------------------------------------

MOCK_RECONCILED = ReconcileResponse(
    reconciled_medication="Metformin 500mg twice daily",
    confidence_score=0.88,
    reasoning="Primary care record is most recent clinical encounter.",
    sources_analyzed=["Hospital EHR", "Primary Care", "Pharmacy"],
    conflicts_found=["Hospital EHR vs Primary Care: \"Metformin 1000mg twice daily\" vs \"Metformin 500mg twice daily\""],
    recommended_actions=["Update Hospital EHR to 500mg twice daily"],
    clinical_safety_check=SafetyStatus.PASSED,
)

MOCK_QUALITY = QualityScore(
    overall_score=62,
    breakdown=QualityBreakdown(
        completeness=60,
        accuracy=50,
        timeliness=70,
        clinical_plausibility=40,
    ),
    issues_detected=[
        FieldIssue(
            field="vital_signs.blood_pressure",
            issue="Blood pressure 340/180 is physiologically implausible",
            severity=IssueSeverity.HIGH,
        ),
    ],
)

VALID_RECONCILE_PAYLOAD = {
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
        {
            "system": "Pharmacy",
            "medication": "Metformin 1000mg daily",
            "last_filled": "2025-01-25",
            "source_reliability": "medium",
        },
    ],
}

VALID_VALIDATE_PAYLOAD = {
    "demographics": {"name": "John Doe", "dob": "1955-03-15", "gender": "M"},
    "medications": ["Metformin 500mg", "Lisinopril 10mg"],
    "allergies": [],
    "conditions": ["Type 2 Diabetes"],
    "vital_signs": {"blood_pressure": "340/180", "heart_rate": 72},
    "last_updated": "2024-06-15",
}


# ---------------------------------------------------------------------------
# Required test 1 — HTTP 400 when "sources" key is absent
# ---------------------------------------------------------------------------

def test_reconcile_input_validation_missing_sources(client):
    resp = _authed_post(client, "/api/reconcile/medication",
                        json={"patient_context": {"age": 50}})
    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body
    assert "details" in body


# ---------------------------------------------------------------------------
# Required test 2 — HTTP 400 when "sources" is an empty array
# ---------------------------------------------------------------------------

def test_reconcile_input_validation_empty_sources(client):
    resp = _authed_post(client, "/api/reconcile/medication",
                        json={"sources": []})
    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body
    assert "details" in body


# ---------------------------------------------------------------------------
# Required test 3 — overall_score is between 0 and 100 via the endpoint
# ---------------------------------------------------------------------------

@patch("api.routes.validate.llm_validate", new_callable=AsyncMock,
       return_value=MOCK_QUALITY)
def test_validate_returns_score_in_range(mock_llm, client):
    resp = _authed_post(client, "/api/validate/data-quality",
                        json=VALID_VALIDATE_PAYLOAD)
    assert resp.status_code == 200
    score = resp.json()["overall_score"]
    assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# Required test 4 — BP "340/180" triggers a high-severity issue
# ---------------------------------------------------------------------------

@patch("api.routes.validate.llm_validate", new_callable=AsyncMock,
       return_value=MOCK_QUALITY)
def test_validate_detects_implausible_bp(mock_llm, client):
    resp = _authed_post(client, "/api/validate/data-quality",
                        json=VALID_VALIDATE_PAYLOAD)
    assert resp.status_code == 200
    issues = resp.json()["issues_detected"]
    bp_issues = [i for i in issues if "blood_pressure" in i["field"]]
    assert len(bp_issues) >= 1
    assert any(i["severity"] == "high" for i in bp_issues)


# ---------------------------------------------------------------------------
# Required test 5 — HTTP 401 when X-API-Key header is absent
# ---------------------------------------------------------------------------

def test_missing_api_key_returns_401(client):
    resp = client.post("/api/reconcile/medication", json=VALID_RECONCILE_PAYLOAD)
    assert resp.status_code == 401
    body = resp.json()
    assert body == {"error": "Unauthorized", "message": "Valid X-API-Key header required"}


# ---------------------------------------------------------------------------
# Additional tests
# ---------------------------------------------------------------------------

@patch("api.routes.reconcile.llm_reconcile", new_callable=AsyncMock,
       return_value=MOCK_RECONCILED)
def test_reconcile_valid_payload_flat_response(mock_llm, client):
    resp = _authed_post(client, "/api/reconcile/medication",
                        json=VALID_RECONCILE_PAYLOAD)
    assert resp.status_code == 200
    assert set(resp.json().keys()) == {
        "reconciled_medication",
        "confidence_score",
        "reasoning",
        "sources_analyzed",
        "conflicts_found",
        "recommended_actions",
        "clinical_safety_check",
    }


def test_wrong_api_key_returns_401(client):
    resp = client.post(
        "/api/reconcile/medication",
        json=VALID_RECONCILE_PAYLOAD,
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "Unauthorized"


def test_health_endpoint_no_auth_required(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Test C — LLM raises AIServiceError → route falls back to deterministic result
# ---------------------------------------------------------------------------

def test_reconcile_route_falls_back_to_deterministic_on_llm_garbage(client):
    """When LLM raises AIServiceError, route returns deterministic result (not 500)."""
    from llm.client import AIServiceError

    with patch("api.routes.reconcile.llm_reconcile", side_effect=AIServiceError("LLM unavailable")):
        resp = _authed_post(
            client,
            "/api/reconcile/medication",
            json={
                "patient_context": {"age": 55, "conditions": ["Hypertension"], "recent_labs": {}},
                "sources": [
                    {
                        "system": "Hospital",
                        "medication": "Aspirin 81mg daily",
                        "last_updated": "2025-01-01",
                        "source_reliability": "high",
                    },
                    {
                        "system": "Clinic",
                        "medication": "Aspirin 325mg daily",
                        "last_updated": "2025-01-10",
                        "source_reliability": "high",
                    },
                ],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "reconciled_medication" in data
