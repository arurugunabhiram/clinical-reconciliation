"""Deterministic medication reconciliation logic.

Picks the best medication record by source reliability then recency,
computes a base confidence score, and runs basic safety checks against
patient context.  Falls back to the LLM layer only when sources conflict
in ways the rule engine cannot resolve.
"""

from __future__ import annotations

from datetime import date, timedelta

from schemas.reconcile import (
    MedicationSource,
    PatientContext,
    ReconciledMedication,
    SafetyStatus,
    SourceReliability,
)

_RELIABILITY_RANK = {
    SourceReliability.HIGH: 3,
    SourceReliability.MEDIUM: 2,
    SourceReliability.LOW: 1,
}

_STALE_THRESHOLD = timedelta(days=180)

# Simple contraindication table: condition → set of drugs to flag.
_CONTRAINDICATIONS: dict[str, set[str]] = {
    "ckd stage 3": {"metformin", "nsaid", "ibuprofen", "naproxen"},
    "ckd stage 4": {"metformin", "nsaid", "ibuprofen", "naproxen"},
    "ckd stage 5": {"metformin", "nsaid", "ibuprofen", "naproxen"},
    "liver cirrhosis": {"acetaminophen", "paracetamol", "methotrexate"},
    "heart failure": {"nsaid", "ibuprofen", "naproxen", "pioglitazone"},
    "pregnancy": {"warfarin", "methotrexate", "lisinopril", "losartan"},
}


def _sort_key(src: MedicationSource) -> tuple[int, date]:
    return (_RELIABILITY_RANK[src.reliability], src.last_updated)


def sources_agree(sources: list[MedicationSource]) -> bool:
    """True when all sources describe the same drug+dose+frequency."""
    first = sources[0]
    return all(
        s.drug_name.lower() == first.drug_name.lower()
        and s.dose.lower() == first.dose.lower()
        and s.frequency.lower() == first.frequency.lower()
        for s in sources[1:]
    )


def _agreement_ratio(sources: list[MedicationSource]) -> float:
    """Fraction of sources matching the most common drug+dose+frequency."""
    if len(sources) <= 1:
        return 1.0
    combos: dict[tuple[str, str, str], int] = {}
    for s in sources:
        key = (s.drug_name.lower(), s.dose.lower(), s.frequency.lower())
        combos[key] = combos.get(key, 0) + 1
    return max(combos.values()) / len(sources)


def _check_safety(
    drug_name: str, patient_ctx: PatientContext
) -> SafetyStatus:
    drug_lower = drug_name.lower()
    for condition in patient_ctx.conditions:
        flagged_drugs = _CONTRAINDICATIONS.get(condition.lower(), set())
        if drug_lower in flagged_drugs:
            return SafetyStatus.FAILED
        # Partial match (e.g. "metformin 500mg" contains "metformin")
        if any(d in drug_lower for d in flagged_drugs):
            return SafetyStatus.WARNING
    return SafetyStatus.PASSED


def _base_confidence(
    best: MedicationSource,
    sources: list[MedicationSource],
    safety: SafetyStatus = SafetyStatus.PASSED,
    today: date | None = None,
) -> float:
    today = today or date.today()
    ratio = _agreement_ratio(sources)

    # Base score from agreement level
    if ratio >= 1.0:          # all sources agree
        score = 0.92
    elif ratio > 0.5:         # majority agree (e.g. 2 of 3)
        score = 0.75
    else:                     # all disagree or no majority
        score = 0.55

    # Adjust by best source reliability
    if best.reliability == SourceReliability.HIGH:
        score += 0.05
    elif best.reliability == SourceReliability.LOW:
        score -= 0.05

    # Penalize stale data
    age = today - best.last_updated
    if age > _STALE_THRESHOLD:
        score -= 0.15

    # Penalize safety failures
    if safety == SafetyStatus.FAILED:
        score -= 0.10

    return round(min(max(score, 0.0), 1.0), 2)


def reconcile_medications(
    sources: list[MedicationSource],
    patient_ctx: PatientContext,
) -> ReconciledMedication:
    """Return a deterministic reconciliation based on source reliability and recency."""
    ranked = sorted(sources, key=_sort_key, reverse=True)
    best = ranked[0]

    reconciled_med = f"{best.drug_name} {best.dose} {best.frequency}"
    safety = _check_safety(best.drug_name, patient_ctx)
    confidence = _base_confidence(best, sources, safety)

    actions: list[str] = ["Verify reconciled medication with patient at next visit"]
    if safety == SafetyStatus.WARNING:
        actions.insert(0, f"Review {best.drug_name} — potential concern given patient conditions")
    elif safety == SafetyStatus.FAILED:
        actions.insert(0, f"URGENT: {best.drug_name} may be contraindicated — escalate to prescriber")

    if not sources_agree(sources):
        actions.append("Reconcile discrepancy across source systems")

    reasoning = (
        f"Selected {best.source_name} (reliability={best.reliability.value}, "
        f"updated={best.last_updated}) as the most authoritative source. "
    )
    if sources_agree(sources):
        reasoning += "All sources agree on drug, dose, and frequency."
    else:
        reasoning += "Sources disagree; the highest-ranked source was preferred."

    return ReconciledMedication(
        reconciled_medication=reconciled_med,
        confidence_score=confidence,
        reasoning=reasoning,
        recommended_actions=actions,
        clinical_safety_check=safety,
    )
