"""Anthropic client wrapper with retry and error handling."""

from __future__ import annotations

import json
import os
import logging

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from schemas.reconcile import MedicationSource, PatientContext, ReconciledMedication
from schemas.validate import PatientRecord, QualityScore
from llm.prompts import (
    RECONCILIATION_SYSTEM,
    VALIDATION_SYSTEM,
    build_reconciliation_user_prompt,
    build_validation_user_prompt,
)
from llm.parser import parse_reconciliation_response, parse_validation_response

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)


def _format_sources(sources: list[MedicationSource]) -> str:
    lines: list[str] = []
    for i, s in enumerate(sources, 1):
        lines.append(
            f"{i}. {s.source_name}: {s.drug_name} {s.dose} {s.frequency} "
            f"(reliability={s.reliability.value}, updated={s.last_updated})"
        )
    return "\n".join(lines)


def _format_patient_context(ctx: PatientContext) -> str:
    parts: list[str] = []
    if ctx.age:
        parts.append(f"Age: {ctx.age}")
    if ctx.conditions:
        parts.append(f"Conditions: {', '.join(ctx.conditions)}")
    if ctx.allergies:
        parts.append(f"Allergies: {', '.join(ctx.allergies)}")
    if ctx.lab_values:
        labs = ", ".join(f"{k}={v}" for k, v in ctx.lab_values.items())
        parts.append(f"Lab values: {labs}")
    return "\n".join(parts) if parts else "No additional context provided."


def _format_patient_record(record: PatientRecord) -> str:
    parts: list[str] = []
    if record.patient_id:
        parts.append(f"Patient ID: {record.patient_id}")
    if record.first_name or record.last_name:
        parts.append(f"Name: {record.first_name or ''} {record.last_name or ''}".strip())
    if record.date_of_birth:
        parts.append(f"Date of Birth: {record.date_of_birth}")
    if record.gender:
        parts.append(f"Gender: {record.gender}")
    if record.medications:
        meds = json.dumps(record.medications, default=str)
        parts.append(f"Medications: {meds}")
    if record.diagnoses:
        parts.append(f"Diagnoses: {', '.join(record.diagnoses)}")
    if record.allergies:
        parts.append(f"Allergies: {', '.join(record.allergies)}")
    else:
        parts.append("Allergies: (none documented)")
    if record.vital_signs:
        vitals = json.dumps(record.vital_signs, default=str)
        parts.append(f"Vital Signs: {vitals}")
    if record.lab_results:
        labs = ", ".join(f"{k}={v}" for k, v in record.lab_results.items())
        parts.append(f"Lab Results: {labs}")
    if record.last_updated:
        parts.append(f"Last Updated: {record.last_updated}")
    return "\n".join(parts) if parts else "Empty record."


@retry(
    retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
)
def _call_anthropic(system: str, user_message: str) -> str:
    client = _get_client()
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def llm_reconcile(
    sources: list[MedicationSource],
    patient_ctx: PatientContext,
) -> ReconciledMedication:
    """Call the LLM to reconcile conflicting medication sources."""
    sources_text = _format_sources(sources)
    context_text = _format_patient_context(patient_ctx)
    user_prompt = build_reconciliation_user_prompt(sources_text, context_text)

    logger.info("Calling LLM for medication reconciliation")
    raw = _call_anthropic(RECONCILIATION_SYSTEM, user_prompt)
    return parse_reconciliation_response(raw)


def llm_validate(record: PatientRecord) -> QualityScore:
    """Call the LLM to evaluate data quality across four dimensions."""
    from datetime import date as _date

    record_json = record.model_dump_json(indent=2)
    current_date = _date.today().isoformat()
    user_prompt = build_validation_user_prompt(record_json, current_date)

    logger.info("Calling LLM for data quality validation")
    raw = _call_anthropic(VALIDATION_SYSTEM, user_prompt)
    return parse_validation_response(raw)
