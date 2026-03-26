from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceReliability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SafetyStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class MedicationSource(BaseModel):
    source_name: str = Field(..., examples=["Hospital EHR"])
    drug_name: str = Field(..., examples=["Metformin"])
    dose: str = Field(..., examples=["500mg"])
    frequency: str = Field(..., examples=["twice daily"])
    last_updated: date
    reliability: SourceReliability = SourceReliability.MEDIUM


class PatientContext(BaseModel):
    age: Optional[int] = None
    conditions: list[str] = Field(default_factory=list, examples=[["Type 2 Diabetes", "CKD Stage 3"]])
    allergies: list[str] = Field(default_factory=list)
    lab_values: dict[str, str] = Field(default_factory=dict, examples=[{"eGFR": "45 mL/min"}])


class ReconcileRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    sources: list[MedicationSource] = Field(..., min_length=2)
    patient_context: PatientContext = Field(default_factory=PatientContext)


class ReconciledMedication(BaseModel):
    reconciled_medication: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    recommended_actions: list[str]
    clinical_safety_check: SafetyStatus


class ReconcileResponse(BaseModel):
    patient_id: str
    result: ReconciledMedication
    source_count: int
    llm_used: bool
