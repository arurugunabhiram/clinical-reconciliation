from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PatientRecord(BaseModel):
    demographics: Optional[dict[str, Any]] = None
    medications: list[Any] = Field(default_factory=list)
    allergies: list[Any] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    vital_signs: dict[str, Any] = Field(default_factory=dict)
    last_updated: Optional[str] = None


class FieldIssue(BaseModel):
    field: str
    issue: str
    severity: IssueSeverity


class QualityBreakdown(BaseModel):
    completeness: int = Field(..., ge=0, le=100)
    accuracy: int = Field(..., ge=0, le=100)
    timeliness: int = Field(..., ge=0, le=100)
    clinical_plausibility: int = Field(..., ge=0, le=100)


class QualityScore(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    breakdown: QualityBreakdown
    issues_detected: list[FieldIssue]


class ValidateResponse(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    breakdown: QualityBreakdown
    issues_detected: list[FieldIssue]
