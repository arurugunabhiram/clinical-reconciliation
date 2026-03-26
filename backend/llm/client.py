"""Anthropic client wrapper with retry and error handling."""

from __future__ import annotations

import json
import os
import logging

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from schemas.reconcile import MedicationSource, PatientContext, ReconciledMedication
from llm.prompts import RECONCILIATION_SYSTEM, build_reconciliation_user_prompt
from llm.parser import parse_reconciliation_response

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
