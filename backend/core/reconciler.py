"""Deterministic medication reconciliation engine."""

from __future__ import annotations

from datetime import date, timedelta

from schemas.reconcile import (
    MedicationSource,
    PatientContext,
    ReconcileResponse,
    SafetyStatus,
    SourceReliability,
)

_STALE_THRESHOLD = timedelta(days=180)

_RENAL_FLAGGED = {"metformin"}
_NSAID_FLAGGED = {"ibuprofen", "naproxen", "aspirin"}


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _effective_date(s: MedicationSource) -> date:
    """Return the most recent valid date from a source, or date.min if none."""
    candidates = [d for d in (_parse_date(s.last_updated), _parse_date(s.last_filled)) if d]
    return max(candidates) if candidates else date.min


def build_conflicts(sources: list[MedicationSource]) -> list[str]:
    """Return human-readable conflict descriptions for every differing source pair."""
    return [
        f"{sources[i].system} vs {sources[j].system}: "
        f'"{sources[i].medication}" vs "{sources[j].medication}"'
        for i in range(len(sources))
        for j in range(i + 1, len(sources))
        if sources[i].medication.strip().lower() != sources[j].medication.strip().lower()
    ]


def sources_agree(sources: list[MedicationSource]) -> bool:
    """Return True if all sources report the same medication string (case-insensitive)."""
    meds = {s.medication.strip().lower() for s in sources}
    return len(meds) == 1


def _agreement_ratio(sources: list[MedicationSource]) -> float:
    """Fraction of sources that agree with the most common medication value."""
    if not sources:
        return 0.0
    counts: dict[str, int] = {}
    for s in sources:
        key = s.medication.strip().lower()
        counts[key] = counts.get(key, 0) + 1
    return max(counts.values()) / len(sources)


def _reliability_rank(r: SourceReliability) -> int:
    return {SourceReliability.HIGH: 2, SourceReliability.MEDIUM: 1, SourceReliability.LOW: 0}[r]


def _sort_key(s: MedicationSource):
    return (_reliability_rank(s.source_reliability), _effective_date(s))


def _check_safety(medication: str, ctx: PatientContext) -> SafetyStatus:
    med_lower = medication.lower()
    conditions_lower = [c.lower() for c in ctx.conditions]
    labs = ctx.recent_labs or {}

    egfr_val = None
    for key in ("eGFR", "egfr", "eGFR_mL/min"):
        raw = labs.get(key)
        if raw is not None:
            try:
                egfr_val = float(str(raw).split()[0])
            except (ValueError, AttributeError):
                pass
            break

    if egfr_val is not None and egfr_val < 45:
        for drug in _RENAL_FLAGGED:
            if drug in med_lower:
                return SafetyStatus.REVIEW_REQUIRED

    has_ckd = any("ckd" in c or "kidney" in c or "renal" in c for c in conditions_lower)
    has_htn = any("hypertension" in c for c in conditions_lower)
    if has_ckd or has_htn:
        for drug in _NSAID_FLAGGED:
            if drug in med_lower:
                return SafetyStatus.REVIEW_REQUIRED

    return SafetyStatus.PASSED


def _base_confidence(
    best: MedicationSource,
    sources: list[MedicationSource],
    safety: SafetyStatus = SafetyStatus.PASSED,
    today: date | None = None,
) -> float:
    today = today or date.today()
    ratio = _agreement_ratio(sources)

    if ratio >= 1.0:
        score = 0.92
    elif ratio > 0.5:
        score = 0.75
    else:
        score = 0.55

    if best.source_reliability == SourceReliability.HIGH:
        score += 0.05
    elif best.source_reliability == SourceReliability.LOW:
        score -= 0.05

    eff = _effective_date(best)
    if eff != date.min and (today - eff) > _STALE_THRESHOLD:
        score -= 0.15

    if safety == SafetyStatus.REVIEW_REQUIRED:
        score -= 0.10

    return round(min(max(score, 0.0), 1.0), 2)


def reconcile_medications(
    sources: list[MedicationSource],
    patient_ctx: PatientContext | None,
) -> ReconcileResponse:
    """Return a deterministic reconciliation based on source reliability and recency."""
    ctx = patient_ctx or PatientContext()
    ranked = sorted(sources, key=_sort_key, reverse=True)
    best = ranked[0]

    safety = _check_safety(best.medication, ctx)
    confidence = _base_confidence(best, sources, safety)

    actions: list[str] = ["Verify reconciled medication with patient at next visit"]
    if safety == SafetyStatus.REVIEW_REQUIRED:
        actions.insert(0, "Review medication — clinical concern flagged; escalate to prescriber")

    if not sources_agree(sources):
        actions.append("Reconcile discrepancy across source systems")

    eff = _effective_date(best)
    date_str = eff.isoformat() if eff != date.min else "unknown"
    reasoning = (
        f"Selected {best.system} (reliability={best.source_reliability.value}, "
        f"date={date_str}) as the most authoritative source. "
    )
    if sources_agree(sources):
        reasoning += "All sources agree on medication."
    else:
        reasoning += "Sources disagree; the highest-ranked source was preferred."

    return ReconcileResponse(
        reconciled_medication=best.medication,
        confidence_score=confidence,
        reasoning=reasoning,
        sources_analyzed=[s.system for s in sources],
        conflicts_found=build_conflicts(sources),
        recommended_actions=actions,
        clinical_safety_check=safety,
    )
