import pytest

from llm.parser import (
    parse_reconciliation_response,
    parse_validation_response,
    LLMParseError,
    _extract_json,
)
from schemas.reconcile import SafetyStatus


_VALID_JSON = '''{
  "reconciled_medication": "Metformin 500mg twice daily",
  "confidence_score": 0.85,
  "reasoning": "Selected Hospital EHR as most reliable. All sources agree on drug and dose.",
  "recommended_actions": ["Verify with patient", "Update pharmacy records"],
  "clinical_safety_check": "PASSED"
}'''


def test_parse_valid_json():
    result = parse_reconciliation_response(_VALID_JSON)
    assert result.reconciled_medication == "Metformin 500mg twice daily"
    assert result.confidence_score == 0.85
    assert result.clinical_safety_check == SafetyStatus.PASSED
    assert len(result.recommended_actions) == 2


def test_parse_json_in_markdown_fence():
    wrapped = f"Here is the result:\n```json\n{_VALID_JSON}\n```\n"
    result = parse_reconciliation_response(wrapped)
    assert result.reconciled_medication == "Metformin 500mg twice daily"


def test_parse_json_with_preamble():
    with_preamble = f"Based on my analysis:\n{_VALID_JSON}"
    result = parse_reconciliation_response(with_preamble)
    assert result.confidence_score == 0.85


def test_parse_rejects_no_json():
    with pytest.raises(LLMParseError, match="No JSON object found"):
        parse_reconciliation_response("I cannot help with that.")


def test_parse_rejects_invalid_json():
    with pytest.raises(LLMParseError, match="Invalid JSON"):
        parse_reconciliation_response('{"broken: json}')


def test_parse_rejects_missing_fields():
    incomplete = '{"reconciled_medication": "Aspirin 81mg daily"}'
    with pytest.raises(LLMParseError, match="Schema validation failed"):
        parse_reconciliation_response(incomplete)


def test_parse_rejects_bad_confidence_range():
    bad = _VALID_JSON.replace('"confidence_score": 0.85', '"confidence_score": 1.5')
    with pytest.raises(LLMParseError, match="Schema validation failed"):
        parse_reconciliation_response(bad)


def test_extract_json_bare_object():
    assert _extract_json('{"a": 1}') == '{"a": 1}'


def test_extract_json_fenced():
    text = "```json\n{\"a\": 1}\n```"
    assert _extract_json(text) == '{"a": 1}'


# ── Validation parser tests ──────────────────────────────────────────

_VALID_VALIDATION_JSON = '''{
  "overall_score": 62,
  "breakdown": {
    "completeness": 60,
    "accuracy": 50,
    "timeliness": 70,
    "clinical_plausibility": 40
  },
  "issues_detected": [
    {
      "field": "vital_signs.blood_pressure",
      "issue": "Systolic BP 340 is clinically impossible",
      "severity": "high"
    }
  ]
}'''


def test_parse_validation_valid_json():
    result = parse_validation_response(_VALID_VALIDATION_JSON)
    assert result.overall_score == 62
    assert result.breakdown.completeness == 60
    assert result.breakdown.accuracy == 50
    assert result.breakdown.timeliness == 70
    assert result.breakdown.clinical_plausibility == 40
    assert result.grade == "D"
    assert len(result.issues_detected) == 1


def test_parse_validation_assigns_grade():
    high_score = _VALID_VALIDATION_JSON.replace('"overall_score": 62', '"overall_score": 92')
    result = parse_validation_response(high_score)
    assert result.grade == "A"


def test_parse_validation_rejects_missing_breakdown():
    bad = '{"overall_score": 50, "issues_detected": []}'
    with pytest.raises(LLMParseError, match="Schema validation failed"):
        parse_validation_response(bad)
