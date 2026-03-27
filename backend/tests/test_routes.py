"""Integration tests for API routes using FastAPI TestClient."""

from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from schemas.reconcile import ReconciledMedication
from schemas.validate import QualityScore, QualityBreakdown, FieldIssue


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """TestClient with no API_KEY enforced (dev mode)."""
    with patch.dict(os.environ, {"API_KEY": ""}, clear=False):
        from main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def auth_client():
    """TestClient with API_KEY enforced."""
    with patch.dict(os.environ, {"API_KEY": "test-key"}, clear=False):
        from main import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Helpers — mock return values
# ---------------------------------------------------------------------------

MOCK_RECONCILED = ReconciledMedication(
    reconciled_medication="Metformin 1000mg twice daily",
    confidence_score=0.85,
    reasoning="Pharmacy record is more recent and from a high-reliability source.",
    recommended_actions=["Confirm dose with patient", "Update EHR"],
    clinical_safety_check="PASSED",
)

MOCK_QUALITY = QualityScore(
    overall_score=82,
    breakdown=QualityBreakdown(
        completeness=80,
        accuracy=85,
        timeliness=78,
        clinical_plausibility=85,
    ),
    issues_detected=[
        FieldIssue(field="allergies", issue="No allergies documented", severity="medium"),
    ],
    grade="B",
)

VALID_RECONCILE_PAYLOAD = {
    "patient_id": "P-001",
    "sources": [
        {
            "source_name": "Hospital EHR",
            "drug_name": "Metformin",
            "dose": "1000mg",
            "frequency": "twice daily",
            "last_updated": "2024-12-01",
            "reliability": "high",
        },
        {
            "source_name": "Patient Report",
            "drug_name": "Metformin",
            "dose": "500mg",
            "frequency": "once daily",
            "last_updated": "2024-06-15",
            "reliability": "low",
        },
    ],
    "patient_context": {
        "age": 62,
        "conditions": ["Type 2 Diabetes"],
        "allergies": [],
        "lab_values": {"HbA1c": "7.2"},
    },
}

VALID_VALIDATE_PAYLOAD = {
    "record": {
        "patient_id": "P-002",
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1960-05-14",
        "gender": "female",
        "medications": [{"name": "Lisinopril", "dose": "10mg", "frequency": "daily"}],
        "diagnoses": ["Hypertension"],
        "allergies": ["Penicillin"],
        "vital_signs": {"blood_pressure": "130/85", "heart_rate": 72},
        "lab_results": {"eGFR": "65 mL/min"},
        "last_updated": "2024-11-01",
    }
}


# ---------------------------------------------------------------------------
# 1. POST /api/reconcile/medication — valid payload → 200
# ---------------------------------------------------------------------------

@patch("api.routes.reconcile.llm_reconcile", return_value=MOCK_RECONCILED)
def test_reconcile_valid_payload(mock_llm, client):
    resp = client.post("/api/reconcile/medication", json=VALID_RECONCILE_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == "P-001"
    assert "result" in data
    assert data["source_count"] == 2
    assert "confidence_score" in data["result"]
    assert "reconciled_medication" in data["result"]
    assert "clinical_safety_check" in data["result"]


# ---------------------------------------------------------------------------
# 2. POST /api/reconcile/medication — only 1 source → 422
# ---------------------------------------------------------------------------

def test_reconcile_single_source_422(client):
    payload = {
        "patient_id": "P-001",
        "sources": [
            {
                "source_name": "Hospital EHR",
                "drug_name": "Metformin",
                "dose": "1000mg",
                "frequency": "twice daily",
                "last_updated": "2024-12-01",
                "reliability": "high",
            },
        ],
    }
    resp = client.post("/api/reconcile/medication", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. POST /api/reconcile/medication — missing patient_id → 422
# ---------------------------------------------------------------------------

def test_reconcile_missing_patient_id_422(client):
    payload = {
        "sources": [
            {
                "source_name": "Hospital EHR",
                "drug_name": "Metformin",
                "dose": "1000mg",
                "frequency": "twice daily",
                "last_updated": "2024-12-01",
                "reliability": "high",
            },
            {
                "source_name": "Pharmacy",
                "drug_name": "Metformin",
                "dose": "500mg",
                "frequency": "once daily",
                "last_updated": "2024-06-15",
                "reliability": "medium",
            },
        ],
    }
    resp = client.post("/api/reconcile/medication", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. POST /api/validate/data-quality — valid record → 200 with overall_score
# ---------------------------------------------------------------------------

@patch("api.routes.validate.llm_validate", return_value=MOCK_QUALITY)
def test_validate_valid_record(mock_llm, client):
    resp = client.post("/api/validate/data-quality", json=VALID_VALIDATE_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == "P-002"
    assert "quality" in data
    score = data["quality"]["overall_score"]
    assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# 5. POST /api/validate/data-quality — empty record body → 422
# ---------------------------------------------------------------------------

def test_validate_empty_body_422(client):
    resp = client.post("/api/validate/data-quality", json={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 6. GET /health → {"status": "ok"}
# ---------------------------------------------------------------------------

def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 7. POST /api/reconcile/medication — invalid API key → 401
# ---------------------------------------------------------------------------

@patch("api.routes.reconcile.llm_reconcile", return_value=MOCK_RECONCILED)
def test_reconcile_invalid_api_key_401(mock_llm, auth_client):
    resp = auth_client.post(
        "/api/reconcile/medication",
        json=VALID_RECONCILE_PAYLOAD,
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


@patch("api.routes.reconcile.llm_reconcile", return_value=MOCK_RECONCILED)
def test_reconcile_missing_api_key_401(mock_llm, auth_client):
    resp = auth_client.post(
        "/api/reconcile/medication",
        json=VALID_RECONCILE_PAYLOAD,
    )
    assert resp.status_code == 401
