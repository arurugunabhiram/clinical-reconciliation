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

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ── Completeness (0-100) ──────────────────────────────────────────────

def _score_completeness(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    present = 0
    total = 6  # demographics, medications, conditions, allergies, vital_signs, last_updated

    demo = record.demographics or {}
    if demo.get("name") or demo.get("dob"):
        present += 1
    else:
        issues.append(FieldIssue(
            field="demographics",
            issue="Demographics (name/dob) missing",
            severity=IssueSeverity.HIGH,
        ))

    if record.medications:
        present += 1
    else:
        issues.append(FieldIssue(
            field="medications",
            issue="No medications listed",
            severity=IssueSeverity.MEDIUM,
        ))

    if record.conditions:
        present += 1
    else:
        issues.append(FieldIssue(
            field="conditions",
            issue="No conditions listed",
            severity=IssueSeverity.MEDIUM,
        ))

    if record.allergies:
        present += 1
    else:
        issues.append(FieldIssue(
            field="allergies",
            issue="No allergies documented — confirm with patient",
            severity=IssueSeverity.LOW,
        ))

    if record.vital_signs:
        present += 1
    else:
        issues.append(FieldIssue(
            field="vital_signs",
            issue="No vital signs recorded",
            severity=IssueSeverity.MEDIUM,
        ))

    if record.last_updated:
        present += 1
    # timeliness handles the score penalty; no duplicate issue here

    score = round((present / total) * 100) if total else 100
    return score, issues


# ── Accuracy (0-100) ──────────────────────────────────────────────────

def _score_accuracy(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    deductions = 0

    dob = (record.demographics or {}).get("dob")
    if dob:
        if _DATE_RE.match(str(dob)):
            try:
                dob_date = datetime.strptime(str(dob), "%Y-%m-%d").date()
                if dob_date > date.today():
                    issues.append(FieldIssue(
                        field="date_of_birth",
                        issue="Date of birth is in the future",
                        severity=IssueSeverity.HIGH,
                    ))
                    deductions += 20
            except ValueError:
                issues.append(FieldIssue(
                    field="date_of_birth",
                    issue="Invalid date value",
                    severity=IssueSeverity.HIGH,
                ))
                deductions += 15
        else:
            issues.append(FieldIssue(
                field="date_of_birth",
                issue="Date of birth should be YYYY-MM-DD format",
                severity=IssueSeverity.MEDIUM,
            ))
            deductions += 10

    # Duplicate conditions
    if record.conditions:
        lower_conds = [c.lower().strip() for c in record.conditions]
        if len(lower_conds) != len(set(lower_conds)):
            issues.append(FieldIssue(
                field="conditions",
                issue="Duplicate conditions detected",
                severity=IssueSeverity.LOW,
            ))
            deductions += 5

    return max(0, 100 - deductions), issues


# ── Timeliness (0-100) ────────────────────────────────────────────────

def _score_timeliness(record: PatientRecord) -> tuple[int, list[FieldIssue]]:
    issues: list[FieldIssue] = []

    if not record.last_updated:
        return 50, issues  # completeness already flags this missing

    try:
        updated = datetime.strptime(record.last_updated, "%Y-%m-%d").date()
    except ValueError:
        issues.append(FieldIssue(
            field="last_updated",
            issue="Invalid last_updated date format",
            severity=IssueSeverity.MEDIUM,
        ))
        return 50, issues

    days_old = (date.today() - updated).days
    if days_old < 0:
        issues.append(FieldIssue(
            field="last_updated",
            issue="last_updated is in the future",
            severity=IssueSeverity.HIGH,
        ))
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
        issues.append(FieldIssue(
            field="last_updated",
            issue=f"Record is over {days_old // 30} months old",
            severity=IssueSeverity.MEDIUM,
        ))

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
    c_lo, c_hi = _TEMP_CELSIUS_RANGE
    f_lo, f_hi = _TEMP_FAHRENHEIT_RANGE

    in_celsius = c_lo <= value <= c_hi
    in_fahrenheit = f_lo <= value <= f_hi

    if in_celsius and in_fahrenheit:
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
                plausible, _ = _check_temperature(v)
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

    # Drug-disease contraindications
    med_names = _extract_drug_names(record.medications)
    lab_egfr = _get_lab_value(record.vital_signs, "egfr")

    if "metformin" in med_names and lab_egfr is not None and lab_egfr < 30:
        issues.append(FieldIssue(
            field="medications",
            issue="Metformin contraindicated with eGFR < 30",
            severity=IssueSeverity.HIGH,
        ))
        deductions += 25

    return max(0, 100 - deductions), issues


def _extract_drug_names(medications: list) -> set[str]:
    names: set[str] = set()
    for med in medications:
        if isinstance(med, str):
            token = med.strip().split()[0].lower() if med.strip() else ""
            if token:
                names.add(token)
        elif isinstance(med, dict):
            for key in ("drug", "drug_name", "name"):
                if key in med:
                    token = str(med[key]).strip().split()[0].lower()
                    if token:
                        names.add(token)
    return names


def _get_lab_value(labs: dict[str, object], key: str) -> float | None:
    for k, v in labs.items():
        if k.lower() == key.lower():
            try:
                return float(re.sub(r"[^\d.]", "", str(v)))
            except ValueError:
                return None
    return None


# ── Public API ────────────────────────────────────────────────────────

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
    )
