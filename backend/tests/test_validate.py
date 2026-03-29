"""Tests for POST /api/validate/data-quality."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from core.quality_scorer import score_record_quality
from schemas.validate import (
    FieldIssue,
    IssueSeverity,
    PatientRecord,
    QualityBreakdown,
    QualityScore,
)

_API_KEY = "test-key"

VALID_PAYLOAD = {
    "demographics": {"name": "John Doe", "dob": "1955-03-15", "gender": "M"},
    "medications": ["Metformin 500mg", "Lisinopril 10mg"],
    "allergies": [],
    "conditions": ["Type 2 Diabetes"],
    "vital_signs": {"blood_pressure": "340/180", "heart_rate": 72},
    "last_updated": "2024-06-15",
}

MOCK_QUALITY = QualityScore(
    overall_score=62,
    breakdown=QualityBreakdown(
        completeness=60, accuracy=50, timeliness=70, clinical_plausibility=40
    ),
    issues_detected=[
        FieldIssue(
            field="vital_signs.blood_pressure",
            issue="Blood pressure 340/180 is physiologically implausible",
            severity=IssueSeverity.HIGH,
        )
    ],
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


@patch("api.routes.validate.llm_validate", new_callable=AsyncMock,
       return_value=MOCK_QUALITY)
def test_validate_returns_score_in_range(mock_llm, client):
    resp = client.post(
        "/api/validate/data-quality",
        json=VALID_PAYLOAD,
        headers={"X-API-Key": _API_KEY},
    )
    assert resp.status_code == 200
    score = resp.json()["overall_score"]
    assert 0 <= score <= 100


def test_validate_detects_implausible_bp():
    record = PatientRecord(
        vital_signs={"blood_pressure": "340/180"},
    )
    result = score_record_quality(record)
    bp_issues = [i for i in result.issues_detected if i.field == "vital_signs.blood_pressure"]
    assert len(bp_issues) >= 1
    assert any(i.severity == IssueSeverity.HIGH for i in bp_issues)
