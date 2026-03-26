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


def _sources_agree(sources: list[MedicationSource]) -> bool:
    """True when all sources describe the same drug+dose+frequency."""
    first = sources[0]
    return all(
        s.drug_name.lower() == first.drug_name.lower()
        and s.dose.lower() == first.dose.lower()
        and s.frequency.lower() == first.frequency.lower()
        for s in sources[1:]
    )


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
    today: date | None = None,
) -> float:
    today = today or date.today()
    score = 0.7

    # Boost if high-reliability source
    if best.reliability == SourceReliability.HIGH:
        score += 0.15
    elif best.reliability == SourceReliability.MEDIUM:
        score += 0.05

    # Boost if all sources agree
    if _sources_agree(sources):
        score += 0.10

    # Penalize stale data
    age = today - best.last_updated
    if age > _STALE_THRESHOLD:
        score -= 0.20

    return round(min(max(score, 0.0), 1.0), 2)


def reconcile_medications(
    sources: list[MedicationSource],
    patient_ctx: PatientContext,
) -> ReconciledMedication | None:
    """Return a deterministic reconciliation or *None* when the LLM should decide.

    Returns ``None`` when the top two sources have the same reliability and
    recency but disagree on the medication — the caller should then invoke
    the LLM path.
    """
    ranked = sorted(sources, key=_sort_key, reverse=True)
    best = ranked[0]

    # If the top two sources tie on reliability but disagree, defer to LLM.
    if len(ranked) >= 2:
        runner_up = ranked[1]
        same_rank = _RELIABILITY_RANK[best.reliability] == _RELIABILITY_RANK[runner_up.reliability]
        same_date = best.last_updated == runner_up.last_updated
        if same_rank and same_date and not _sources_agree([best, runner_up]):
            return None  # needs LLM

    reconciled_med = f"{best.drug_name} {best.dose} {best.frequency}"
    confidence = _base_confidence(best, sources)
    safety = _check_safety(best.drug_name, patient_ctx)

    actions: list[str] = ["Verify reconciled medication with patient at next visit"]
    if safety == SafetyStatus.WARNING:
        actions.insert(0, f"Review {best.drug_name} — potential concern given patient conditions")
    elif safety == SafetyStatus.FAILED:
        actions.insert(0, f"URGENT: {best.drug_name} may be contraindicated — escalate to prescriber")

    if not _sources_agree(sources):
        actions.append("Reconcile discrepancy across source systems")

    reasoning = (
        f"Selected {best.source_name} (reliability={best.reliability.value}, "
        f"updated={best.last_updated}) as the most authoritative source. "
    )
    if _sources_agree(sources):
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
