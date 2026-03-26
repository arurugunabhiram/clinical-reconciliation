from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PatientRecord(BaseModel):
    patient_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    medications: list[dict] = Field(default_factory=list)
    diagnoses: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    lab_results: dict[str, str] = Field(default_factory=dict)


class ValidateRequest(BaseModel):
    record: PatientRecord


class FieldIssue(BaseModel):
    field: str
    severity: Severity
    message: str


class QualityScore(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)
    consistency_score: float = Field(..., ge=0.0, le=1.0)
    issues: list[FieldIssue]
    grade: str = Field(..., pattern="^(A|B|C|D|F)$")


class ValidateResponse(BaseModel):
    patient_id: Optional[str]
    quality: QualityScore
    llm_used: bool
