"""Deterministic data-quality scoring for patient records (4-dimension model)."""

from __future__ import annotations

import re
from datetime import datetime, date

from schemas.validate import (
    FieldIssue,
    IssueSeverity,
    PatientRecord,
    QualityBreakdown,
    QualityScore,
)

_REQUIRED_FIELDS: list[tuple[str, str]] = [
    ("patient_id", "Patient ID"),
    ("first_name", "First name"),
    ("last_name", "Last name"),
    ("date_of_birth", "Date of birth"),
]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── Completeness (0-100) ──────────────────────────────────────────────

def _score_completeness(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    present = 0
    total = len(_REQUIRED_FIELDS) + 4  # +4 for meds, diagnoses, allergies, vital_signs

    for attr, label in _REQUIRED_FIELDS:
        if getattr(record, attr, None):
            present += 1
        else:
            issues.append(FieldIssue(field=attr, issue=f"{label} is missing", severity=IssueSeverity.HIGH))

    if record.medications:
        present += 1
    else:
        issues.append(FieldIssue(field="medications", issue="No medications listed", severity=IssueSeverity.MEDIUM))

    if record.diagnoses:
        present += 1
    else:
        issues.append(FieldIssue(field="diagnoses", issue="No diagnoses listed", severity=IssueSeverity.MEDIUM))

    if record.allergies:
        present += 1
    else:
        issues.append(FieldIssue(field="allergies", issue="Allergies not documented — confirm with patient", severity=IssueSeverity.LOW))

    if record.vital_signs:
        present += 1
    else:
        issues.append(FieldIssue(field="vital_signs", issue="No vital signs recorded", severity=IssueSeverity.MEDIUM))

    score = round((present / total) * 100) if total else 100
    return score, issues


# ── Accuracy (0-100) ──────────────────────────────────────────────────

def _score_accuracy(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    deductions = 0

    # DOB format and validity
    if record.date_of_birth:
        if _DATE_RE.match(record.date_of_birth):
            try:
                dob = datetime.strptime(record.date_of_birth, "%Y-%m-%d").date()
                if dob > date.today():
                    issues.append(FieldIssue(field="date_of_birth", issue="Date of birth is in the future", severity=IssueSeverity.HIGH))
                    deductions += 20
            except ValueError:
                issues.append(FieldIssue(field="date_of_birth", issue="Invalid date value", severity=IssueSeverity.HIGH))
                deductions += 15
        else:
            issues.append(FieldIssue(field="date_of_birth", issue="Date of birth should be YYYY-MM-DD format", severity=IssueSeverity.MEDIUM))
            deductions += 10

    # Medication entries should have drug/dose info
    for i, med in enumerate(record.medications):
        if isinstance(med, dict):
            if "drug" not in med and "drug_name" not in med:
                issues.append(FieldIssue(
                    field=f"medications[{i}]",
                    issue="Medication entry missing drug name",
                    severity=IssueSeverity.MEDIUM,
                ))
                deductions += 5

    # Duplicate diagnoses
    if record.diagnoses:
        lower_diag = [d.lower().strip() for d in record.diagnoses]
        if len(lower_diag) != len(set(lower_diag)):
            issues.append(FieldIssue(field="diagnoses", issue="Duplicate diagnoses detected", severity=IssueSeverity.LOW))
            deductions += 5

    return max(0, 100 - deductions), issues


# ── Timeliness (0-100) ────────────────────────────────────────────────

def _score_timeliness(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []

    if not record.last_updated:
        issues.append(FieldIssue(field="last_updated", issue="No last_updated date provided", severity=IssueSeverity.MEDIUM))
        return 50, issues

    try:
        updated = datetime.strptime(record.last_updated, "%Y-%m-%d").date()
    except ValueError:
        issues.append(FieldIssue(field="last_updated", issue="Invalid last_updated date format", severity=IssueSeverity.MEDIUM))
        return 50, issues

    days_old = (date.today() - updated).days
    if days_old < 0:
        issues.append(FieldIssue(field="last_updated", issue="last_updated is in the future", severity=IssueSeverity.HIGH))
        return 50, issues

    if days_old <= 30:
        score = 100
    elif days_old <= 90:
        score = 80
    elif days_old <= 180:
        score = 70
    elif days_old <= 365:
        score = 50
    else:
        score = 30
        issues.append(FieldIssue(field="last_updated", issue=f"Record is over {days_old // 30} months old", severity=IssueSeverity.MEDIUM))

    return score, issues


# ── Clinical Plausibility (0-100) ─────────────────────────────────────

_VITAL_RANGES = {
    "heart_rate": (20, 250),
    "spo2": (0, 100),
    "respiratory_rate": (4, 60),
}

_TEMP_CELSIUS_RANGE = (28.0, 45.0)
_TEMP_FAHRENHEIT_RANGE = (85.0, 115.0)


def _check_temperature(value: float) -> tuple[bool, str]:
    """Check whether a temperature is plausible in Celsius or Fahrenheit.

    Returns (is_plausible, detected_unit).
    """
    c_lo, c_hi = _TEMP_CELSIUS_RANGE
    f_lo, f_hi = _TEMP_FAHRENHEIT_RANGE

    in_celsius = c_lo <= value <= c_hi
    in_fahrenheit = f_lo <= value <= f_hi

    if in_celsius and in_fahrenheit:
        # Overlapping range (e.g. 95–115 could be either); assume Fahrenheit
        # since that's more common in clinical systems for values ≥ 85
        return True, "F"
    if in_celsius:
        return True, "C"
    if in_fahrenheit:
        return True, "F"
    return False, "unknown"


def _parse_bp(bp_str: str) -> tuple[int, int] | None:
    m = re.match(r"(\d+)\s*/\s*(\d+)", str(bp_str))
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _score_clinical_plausibility(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    deductions = 0

    # Check vital signs
    for key, value in record.vital_signs.items():
        if key == "blood_pressure":
            bp = _parse_bp(str(value))
            if bp:
                sbp, dbp = bp
                if sbp > 300 or sbp < 50:
                    issues.append(FieldIssue(
                        field="vital_signs.blood_pressure",
                        issue=f"Systolic BP {sbp} is clinically impossible",
                        severity=IssueSeverity.HIGH,
                    ))
                    deductions += 30
                if dbp > 200 or dbp < 20:
                    issues.append(FieldIssue(
                        field="vital_signs.blood_pressure",
                        issue=f"Diastolic BP {dbp} is clinically impossible",
                        severity=IssueSeverity.HIGH,
                    ))
                    deductions += 20
        elif key == "temperature":
            try:
                v = float(value)
                plausible, unit = _check_temperature(v)
                if not plausible:
                    c_lo, c_hi = _TEMP_CELSIUS_RANGE
                    f_lo, f_hi = _TEMP_FAHRENHEIT_RANGE
                    issues.append(FieldIssue(
                        field="vital_signs.temperature",
                        issue=(
                            f"Temperature {v} is outside both plausible Celsius "
                            f"({c_lo}-{c_hi}) and Fahrenheit ({f_lo}-{f_hi}) ranges"
                        ),
                        severity=IssueSeverity.HIGH,
                    ))
                    deductions += 25
            except (ValueError, TypeError):
                pass
        elif key in _VITAL_RANGES:
            try:
                v = float(value)
                lo, hi = _VITAL_RANGES[key]
                if v < lo or v > hi:
                    issues.append(FieldIssue(
                        field=f"vital_signs.{key}",
                        issue=f"{key} value {v} is outside plausible range ({lo}-{hi})",
                        severity=IssueSeverity.HIGH,
                    ))
                    deductions += 25
            except (ValueError, TypeError):
                pass

    # Drug-disease contraindications (basic checks)
    med_names = _extract_drug_names(record.medications)
    lab_egfr = _get_lab_value(record.lab_results, "egfr")

    if "metformin" in med_names and lab_egfr is not None and lab_egfr < 30:
        issues.append(FieldIssue(
            field="medications",
            issue="Metformin contraindicated with eGFR < 30",
            severity=IssueSeverity.HIGH,
        ))
        deductions += 25

    return max(0, 100 - deductions), issues


def _extract_drug_names(medications: list[dict]) -> set[str]:
    names: set[str] = set()
    for med in medications:
        if isinstance(med, dict):
            for key in ("drug", "drug_name", "name"):
                if key in med:
                    names.add(str(med[key]).lower())
    return names


def _get_lab_value(labs: dict[str, str], key: str) -> float | None:
    for k, v in labs.items():
        if k.lower() == key.lower():
            try:
                return float(re.sub(r"[^\d.]", "", str(v)))
            except ValueError:
                return None
    return None


# ── Public API ────────────────────────────────────────────────────────

def _letter_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def score_record_quality(record: PatientRecord) -> QualityScore:
    comp, comp_issues = _score_completeness(record)
    acc, acc_issues = _score_accuracy(record)
    time, time_issues = _score_timeliness(record)
    plaus, plaus_issues = _score_clinical_plausibility(record)

    all_issues = comp_issues + acc_issues + time_issues + plaus_issues
    overall = round(comp * 0.25 + acc * 0.25 + time * 0.25 + plaus * 0.25)

    return QualityScore(
        overall_score=overall,
        breakdown=QualityBreakdown(
            completeness=comp,
            accuracy=acc,
            timeliness=time,
            clinical_plausibility=plaus,
        ),
        issues_detected=all_issues,
        grade=_letter_grade(overall),
    )
