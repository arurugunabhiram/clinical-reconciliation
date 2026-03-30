"""Parse and validate LLM JSON responses."""

from __future__ import annotations

import json
import re

from schemas.reconcile import ReconcileResponse, SafetyStatus
from schemas.validate import QualityScore


class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed into the expected schema."""


def _extract_json(text: str) -> str:
    """Pull a JSON object from text that may contain markdown fences or prose."""
    # First pass: strip markdown fences literally
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    if cleaned.startswith("{"):
        return cleaned

    # Second pass: regex extraction for fences or embedded objects
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    raise LLMParseError("No JSON object found in LLM response")


def parse_reconciliation_response(raw: str) -> ReconcileResponse:
    """Parse raw LLM text into a validated ReconcileResponse."""
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise LLMParseError(f"Invalid JSON: {exc}") from exc

    # Ensure confidence_score is a float, not a string
    if "confidence_score" in data:
        try:
            data["confidence_score"] = float(data["confidence_score"])
        except (TypeError, ValueError):
            data["confidence_score"] = 0.5

    # clinical_safety_check must never be null/missing — default to REVIEW_REQUIRED
    raw_safety = data.get("clinical_safety_check")
    if raw_safety not in ("PASSED", "REVIEW_REQUIRED"):
        data["clinical_safety_check"] = SafetyStatus.REVIEW_REQUIRED.value

    # LLM doesn't produce these fields — default to empty lists so the schema validates
    data.setdefault("sources_analyzed", [])
    data.setdefault("conflicts_found", [])

    try:
        return ReconcileResponse.model_validate(data)
    except Exception as exc:
        raise LLMParseError(f"Schema validation failed: {exc}") from exc


def parse_validation_response(raw: str) -> QualityScore:
    """Parse raw LLM text into a validated QualityScore."""
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise LLMParseError(f"Invalid JSON: {exc}") from exc

    # Coerce all scores to int (LLM sometimes returns floats)
    if "overall_score" in data:
        data["overall_score"] = int(round(float(data["overall_score"])))

    if "breakdown" in data and isinstance(data["breakdown"], dict):
        for key in ("completeness", "accuracy", "timeliness", "clinical_plausibility"):
            if key in data["breakdown"]:
                data["breakdown"][key] = int(round(float(data["breakdown"][key])))

    try:
        return QualityScore.model_validate(data)
    except Exception as exc:
        raise LLMParseError(f"Schema validation failed: {exc}") from exc
