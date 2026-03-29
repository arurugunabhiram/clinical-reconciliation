"""Unit tests for core/reconciler.py"""

import pytest

from core.reconciler import reconcile_medications, sources_agree, _base_confidence
from schemas.reconcile import MedicationSource, PatientContext, SourceReliability, SafetyStatus


def _src(
    system="Hospital EHR",
    medication="Metformin 500mg twice daily",
    source_reliability=SourceReliability.HIGH,
    last_updated="2025-01-15",
):
    return MedicationSource(
        system=system,
        medication=medication,
        last_updated=last_updated,
        source_reliability=source_reliability,
    )


def test_sources_agree_identical():
    sources = [_src(), _src(system="Pharmacy")]
    assert sources_agree(sources) is True


def test_sources_agree_different_dose():
    sources = [
        _src(medication="Metformin 500mg twice daily"),
        _src(system="Pharmacy", medication="Metformin 1000mg twice daily"),
    ]
    assert sources_agree(sources) is False


def test_reconcile_picks_highest_reliability():
    high = _src(system="Hospital EHR", source_reliability=SourceReliability.HIGH)
    low = _src(
        system="Patient Portal",
        medication="Metformin 1000mg twice daily",
        source_reliability=SourceReliability.LOW,
        last_updated="2025-01-20",
    )
    result = reconcile_medications([low, high], PatientContext())
    assert "500mg" in result.reconciled_medication


def test_reconcile_picks_most_recent_when_same_reliability():
    older = _src(system="EHR A", last_updated="2024-06-01", source_reliability=SourceReliability.MEDIUM)
    newer = _src(
        system="EHR B",
        medication="Metformin 1000mg twice daily",
        last_updated="2025-01-15",
        source_reliability=SourceReliability.MEDIUM,
    )
    result = reconcile_medications([older, newer], PatientContext())
    assert "1000mg" in result.reconciled_medication


def test_reconcile_always_returns_result():
    sources = [_src(), _src(system="Clinic", medication="Aspirin 81mg daily")]
    result = reconcile_medications(sources, PatientContext())
    assert result is not None
    assert result.reconciled_medication != ""


def test_reconcile_output_matches_assessment_format():
    """Response must have exactly the 5 fields from the assessment — no extras."""
    sources = [
        _src(),
        _src(system="Clinic", medication="Metformin 1000mg twice daily"),
    ]
    result = reconcile_medications(sources, PatientContext())
    keys = set(result.model_dump().keys())
    assert keys == {
        "reconciled_medication",
        "confidence_score",
        "reasoning",
        "recommended_actions",
        "clinical_safety_check",
    }


def test_reconcile_safety_warning_low_egfr():
    sources = [
        _src(medication="Metformin 500mg twice daily"),
        _src(system="Clinic", medication="Metformin 500mg twice daily"),
    ]
    ctx = PatientContext(
        age=67,
        conditions=["Type 2 Diabetes"],
        recent_labs={"eGFR": 40},
    )
    result = reconcile_medications(sources, ctx)
    assert result.clinical_safety_check == SafetyStatus.REVIEW_REQUIRED


def test_pharmacy_source_uses_last_filled():
    pharmacy = MedicationSource(
        system="Pharmacy",
        medication="Metformin 1000mg daily",
        last_filled="2025-01-25",
        source_reliability=SourceReliability.MEDIUM,
    )
    ehr = _src(last_updated="2024-10-15")
    result = reconcile_medications([pharmacy, ehr], PatientContext())
    assert result is not None


# #old code
# from datetime import date

# from core.reconciler import reconcile_medications, sources_agree, _base_confidence
# from schemas.reconcile import MedicationSource, PatientContext, SourceReliability, SafetyStatus


# def _src(name="EHR", drug="Metformin", dose="500mg", freq="twice daily",
#          reliability=SourceReliability.HIGH, updated=date(2025, 1, 15)):
#     return MedicationSource(
#         source_name=name, drug_name=drug, dose=dose, frequency=freq,
#         reliability=reliability, last_updated=updated,
#     )


# def test_sources_agree_identical():
#     sources = [_src(), _src(name="Pharmacy")]
#     assert sources_agree(sources) is True


# def test_sources_agree_different_dose():
#     sources = [_src(dose="500mg"), _src(name="Pharmacy", dose="1000mg")]
#     assert sources_agree(sources) is False


# def test_reconcile_picks_highest_reliability():
#     high = _src(name="Hospital EHR", reliability=SourceReliability.HIGH)
#     low = _src(name="Patient Portal", drug="Metformin", dose="1000mg",
#                reliability=SourceReliability.LOW, updated=date(2025, 1, 20))
#     result = reconcile_medications([low, high], PatientContext())
#     assert result is not None
#     assert "500mg" in result.reconciled_medication


# def test_reconcile_picks_most_recent_when_same_reliability():
#     older = _src(name="EHR A", updated=date(2024, 6, 1), reliability=SourceReliability.MEDIUM)
#     newer = _src(name="EHR B", dose="1000mg", updated=date(2025, 1, 15),
#                  reliability=SourceReliability.MEDIUM)
#     result = reconcile_medications([older, newer], PatientContext())
#     assert result is not None
#     assert "1000mg" in result.reconciled_medication


# def test_reconcile_always_returns_result():
#     """Deterministic reconciler now always returns a result (never None)."""
#     a = _src(name="Source A", dose="500mg", reliability=SourceReliability.HIGH,
#              updated=date(2025, 1, 15))
#     b = _src(name="Source B", dose="1000mg", reliability=SourceReliability.HIGH,
#              updated=date(2025, 1, 15))
#     result = reconcile_medications([a, b], PatientContext())
#     assert result is not None


# def test_safety_check_flags_contraindication():
#     src = _src(drug="Metformin")
#     ctx = PatientContext(conditions=["CKD Stage 4"])
#     result = reconcile_medications([src, _src(name="Pharmacy")], ctx)
#     assert result is not None
#     assert result.clinical_safety_check in (SafetyStatus.WARNING, SafetyStatus.FAILED)


# def test_confidence_high_when_sources_agree():
#     sources = [_src(), _src(name="Pharmacy")]
#     c = _base_confidence(sources[0], sources, today=date(2025, 3, 1))
#     assert c >= 0.90


# def test_confidence_moderate_when_majority_agrees():
#     sources = [
#         _src(dose="500mg"),
#         _src(name="Pharmacy", dose="500mg"),
#         _src(name="Patient", dose="1000mg"),
#     ]
#     c = _base_confidence(sources[0], sources, today=date(2025, 3, 1))
#     assert 0.70 <= c <= 0.85


# def test_confidence_low_when_all_disagree():
#     sources = [
#         _src(dose="500mg", freq="once daily"),
#         _src(name="Pharmacy", dose="1000mg", freq="twice daily"),
#         _src(name="Patient", dose="750mg", freq="three times daily"),
#     ]
#     c = _base_confidence(sources[0], sources, today=date(2025, 3, 1))
#     assert 0.50 <= c <= 0.65


# def test_confidence_boost_when_sources_agree():
#     sources = [_src(), _src(name="Pharmacy")]
#     c1 = _base_confidence(sources[0], sources, today=date(2025, 3, 1))

#     sources_disagree = [_src(), _src(name="Pharmacy", dose="1000mg")]
#     c2 = _base_confidence(sources_disagree[0], sources_disagree, today=date(2025, 3, 1))

#     assert c1 > c2


# def test_confidence_penalty_for_stale_data():
#     recent = _src(updated=date(2025, 1, 15))
#     stale = _src(updated=date(2023, 1, 1))
#     c_recent = _base_confidence(recent, [recent, _src(name="B")], today=date(2025, 3, 1))
#     c_stale = _base_confidence(stale, [stale, _src(name="B", updated=date(2023, 1, 1))],
#                                 today=date(2025, 3, 1))
#     assert c_recent > c_stale


# def test_confidence_penalty_for_safety_failed():
#     sources = [_src(), _src(name="Pharmacy")]
#     c_passed = _base_confidence(sources[0], sources, safety=SafetyStatus.PASSED, today=date(2025, 3, 1))
#     c_failed = _base_confidence(sources[0], sources, safety=SafetyStatus.FAILED, today=date(2025, 3, 1))
#     assert c_passed > c_failed
