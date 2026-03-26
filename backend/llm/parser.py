"""Parse and validate LLM JSON responses."""

from __future__ import annotations

import json
import re

from schemas.reconcile import ReconciledMedication
from schemas.validate import QualityScore


class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed into the expected schema."""


def _extract_json(text: str) -> str:
    """Pull a JSON object from text that may contain markdown fences or prose."""
    # Try to find a ```json ... ``` block first.
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    # Fall back to the first { ... } block.
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    raise LLMParseError("No JSON object found in LLM response")


def parse_reconciliation_response(raw: str) -> ReconciledMedication:
    """Parse raw LLM text into a validated ReconciledMedication."""
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise LLMParseError(f"Invalid JSON: {exc}") from exc

    try:
        return ReconciledMedication.model_validate(data)
    except Exception as exc:
        raise LLMParseError(f"Schema validation failed: {exc}") from exc


def parse_validation_response(raw: str) -> QualityScore:
    """Parse raw LLM text into a validated QualityScore."""
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise LLMParseError(f"Invalid JSON: {exc}") from exc

    # Map LLM output to our schema (add grade from overall_score)
    overall = data.get("overall_score", 0)
    if overall >= 90:
        grade = "A"
    elif overall >= 80:
        grade = "B"
    elif overall >= 70:
        grade = "C"
    elif overall >= 60:
        grade = "D"
    else:
        grade = "F"

    data["grade"] = grade

    # Rename issues_detected to match schema if already correct
    try:
        return QualityScore.model_validate(data)
    except Exception as exc:
        raise LLMParseError(f"Schema validation failed: {exc}") from exc
