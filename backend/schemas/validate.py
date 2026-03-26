from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PatientRecord(BaseModel):
    patient_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    medications: list[dict] = Field(default_factory=list)
    diagnoses: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    vital_signs: dict[str, object] = Field(default_factory=dict)
    lab_results: dict[str, str] = Field(default_factory=dict)
    last_updated: Optional[str] = None


class ValidateRequest(BaseModel):
    record: PatientRecord


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
    grade: str = Field(..., pattern="^(A|B|C|D|F)$")


class ValidateResponse(BaseModel):
    patient_id: Optional[str]
    quality: QualityScore
    llm_used: bool
