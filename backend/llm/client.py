"""Anthropic async client with retry and error handling."""

from __future__ import annotations

import asyncio
import json
import logging
import os

import anthropic

from schemas.reconcile import MedicationSource, PatientContext, ReconcileResponse
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
_RETRY_DELAYS = [1, 2, 4]  # seconds between attempts on HTTP 429


class AIServiceError(Exception):
    """Raised when the Anthropic API call fails unrecoverably."""


def _get_client() -> anthropic.AsyncAnthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIServiceError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.AsyncAnthropic(api_key=api_key)


def _format_sources(sources: list[MedicationSource]) -> str:
    lines: list[str] = []
    for i, s in enumerate(sources, 1):
        if s.last_filled and not s.last_updated:
            date_label, date_val = "last_filled", s.last_filled
        elif s.last_updated:
            date_label, date_val = "last_updated", s.last_updated
        else:
            date_label, date_val = "date", "unknown"
        lines.append(
            f"{i}. {s.system}: {s.medication} "
            f"({date_label}: {date_val}, source_reliability: {s.source_reliability.value})"
        )
    return "\n".join(lines)


def _format_patient_context(ctx: PatientContext) -> str:
    parts: list[str] = []
    if ctx.age:
        parts.append(f"Age: {ctx.age}")
    if ctx.conditions:
        parts.append(f"Conditions: {', '.join(ctx.conditions)}")
    if ctx.recent_labs:
        labs = ", ".join(f"{k}={v}" for k, v in ctx.recent_labs.items())
        parts.append(f"Recent labs: {labs}")
    return "\n".join(parts) if parts else "No additional context provided."


def _format_patient_record(record: PatientRecord) -> str:
    parts: list[str] = []
    if record.demographics:
        demo = record.demographics
        if demo.get("name"):
            parts.append(f"Name: {demo['name']}")
        if demo.get("dob"):
            parts.append(f"Date of Birth: {demo['dob']}")
        if demo.get("gender"):
            parts.append(f"Gender: {demo['gender']}")
    if record.medications:
        meds = json.dumps(record.medications, default=str)
        parts.append(f"Medications: {meds}")
    if record.conditions:
        parts.append(f"Conditions: {', '.join(record.conditions)}")
    if record.allergies:
        parts.append(f"Allergies: {', '.join(str(a) for a in record.allergies)}")
    else:
        parts.append("Allergies: (none documented)")
    if record.vital_signs:
        vitals = json.dumps(record.vital_signs, default=str)
        parts.append(f"Vital Signs: {vitals}")
    if record.last_updated:
        parts.append(f"Last Updated: {record.last_updated}")
    return "\n".join(parts) if parts else "Empty record."


async def _call_anthropic(system: str, user_message: str) -> str:
    """Call the Anthropic API with up to 3 retries on HTTP 429 (1s, 2s, 4s delays)."""
    client = _get_client()
    last_exc: Exception | None = None

    for attempt, delay in enumerate(_RETRY_DELAYS, 1):
        try:
            response = await client.messages.create(
                model=_MODEL,
                max_tokens=2048,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except anthropic.RateLimitError as exc:
            last_exc = exc
            logger.warning("Rate limit hit (attempt %d/%d), retrying in %ds", attempt, len(_RETRY_DELAYS), delay)
            await asyncio.sleep(delay)
        except anthropic.APIConnectionError as exc:
            raise AIServiceError(f"Network connection to Anthropic API failed: {exc}") from exc
        except anthropic.APIError as exc:
            raise AIServiceError(f"Anthropic API error: {exc}") from exc
        except Exception as exc:
            raise AIServiceError(f"Unexpected error calling Anthropic: {exc}") from exc

    raise AIServiceError(f"Rate limit exceeded after {len(_RETRY_DELAYS)} retries") from last_exc


async def llm_reconcile(
    sources: list[MedicationSource],
    patient_ctx: PatientContext | None,
) -> ReconcileResponse:
    """Call the LLM to reconcile conflicting medication sources."""
    sources_text = _format_sources(sources)
    context_text = _format_patient_context(patient_ctx or PatientContext())
    user_prompt = build_reconciliation_user_prompt(sources_text, context_text)

    logger.info("Calling LLM for medication reconciliation")
    try:
        raw = await _call_anthropic(RECONCILIATION_SYSTEM, user_prompt)
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"llm_reconcile failed: {exc}") from exc

    return parse_reconciliation_response(raw)


async def llm_validate(record: PatientRecord) -> QualityScore:
    """Call the LLM to evaluate data quality across four dimensions."""
    from datetime import date as _date

    record_json = record.model_dump_json(indent=2)
    current_date = _date.today().isoformat()
    user_prompt = build_validation_user_prompt(record_json, current_date)

    logger.info("Calling LLM for data quality validation")
    try:
        raw = await _call_anthropic(VALIDATION_SYSTEM, user_prompt)
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"llm_validate failed: {exc}") from exc

    return parse_validation_response(raw)
