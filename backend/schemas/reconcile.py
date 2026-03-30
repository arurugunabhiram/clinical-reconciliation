from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SourceReliability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SafetyStatus(str, Enum):
    PASSED = "PASSED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class MedicationSource(BaseModel):
    system: str = Field(..., examples=["Hospital EHR"])
    medication: str = Field(..., examples=["Metformin 1000mg twice daily"])
    last_updated: Optional[str] = None
    last_filled: Optional[str] = None
    source_reliability: SourceReliability = SourceReliability.MEDIUM


class PatientContext(BaseModel):
    age: Optional[int] = None
    conditions: list[str] = Field(default_factory=list)
    recent_labs: Optional[dict[str, Any]] = None


class ReconcileRequest(BaseModel):
    patient_context: Optional[PatientContext] = None
    sources: list[MedicationSource] = Field(..., min_length=1)


class ReconcileResponse(BaseModel):
    reconciled_medication: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    sources_analyzed: list[str] = Field(default_factory=list)
    conflicts_found: list[str] = Field(default_factory=list)
    recommended_actions: list[str]
    clinical_safety_check: SafetyStatus = SafetyStatus.REVIEW_REQUIRED
