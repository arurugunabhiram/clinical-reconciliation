"""Deterministic data-quality scoring for patient records."""

from __future__ import annotations

import re
from datetime import datetime

from schemas.validate import FieldIssue, PatientRecord, QualityScore, Severity

_REQUIRED_FIELDS: list[tuple[str, str]] = [
    ("patient_id", "Patient ID"),
    ("first_name", "First name"),
    ("last_name", "Last name"),
    ("date_of_birth", "Date of birth"),
]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_completeness(record: PatientRecord) -> tuple[float, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    present = 0
    total = len(_REQUIRED_FIELDS) + 3  # +3 for medications, diagnoses, allergies

    for attr, label in _REQUIRED_FIELDS:
        value = getattr(record, attr, None)
        if value:
            present += 1
        else:
            issues.append(FieldIssue(field=attr, severity=Severity.ERROR, message=f"{label} is missing"))

    if record.medications:
        present += 1
    else:
        issues.append(FieldIssue(field="medications", severity=Severity.WARNING, message="No medications listed"))

    if record.diagnoses:
        present += 1
    else:
        issues.append(FieldIssue(field="diagnoses", severity=Severity.WARNING, message="No diagnoses listed"))

    if record.allergies:
        present += 1
    else:
        issues.append(FieldIssue(field="allergies", severity=Severity.INFO, message="No allergies listed — confirm with patient"))

    score = round(present / total, 2) if total else 1.0
    return score, issues


def _check_consistency(record: PatientRecord) -> tuple[float, list[FieldIssue]]:
    issues: list[FieldIssue] = []
    checks_passed = 0
    checks_total = 0

    # DOB format
    if record.date_of_birth:
        checks_total += 1
        if _DATE_RE.match(record.date_of_birth):
            try:
                dob = datetime.strptime(record.date_of_birth, "%Y-%m-%d").date()
                if dob > datetime.now().date():
                    issues.append(FieldIssue(field="date_of_birth", severity=Severity.ERROR, message="Date of birth is in the future"))
                else:
                    checks_passed += 1
            except ValueError:
                issues.append(FieldIssue(field="date_of_birth", severity=Severity.ERROR, message="Invalid date value"))
        else:
            issues.append(FieldIssue(field="date_of_birth", severity=Severity.WARNING, message="Date of birth should be in YYYY-MM-DD format"))

    # Medication entries should have drug_name and dose
    for i, med in enumerate(record.medications):
        checks_total += 1
        if "drug_name" in med and "dose" in med:
            checks_passed += 1
        else:
            missing = [k for k in ("drug_name", "dose") if k not in med]
            issues.append(
                FieldIssue(
                    field=f"medications[{i}]",
                    severity=Severity.WARNING,
                    message=f"Medication entry missing: {', '.join(missing)}",
                )
            )

    # Duplicate diagnoses
    if record.diagnoses:
        checks_total += 1
        lower_diag = [d.lower().strip() for d in record.diagnoses]
        if len(lower_diag) == len(set(lower_diag)):
            checks_passed += 1
        else:
            issues.append(FieldIssue(field="diagnoses", severity=Severity.INFO, message="Duplicate diagnoses detected"))

    score = round(checks_passed / checks_total, 2) if checks_total else 1.0
    return score, issues


def _letter_grade(score: float) -> str:
    if score >= 0.90:
        return "A"
    if score >= 0.80:
        return "B"
    if score >= 0.70:
        return "C"
    if score >= 0.60:
        return "D"
    return "F"


def score_record_quality(record: PatientRecord) -> QualityScore:
    comp_score, comp_issues = _check_completeness(record)
    cons_score, cons_issues = _check_consistency(record)
    all_issues = comp_issues + cons_issues
    overall = round((comp_score * 0.6 + cons_score * 0.4), 2)

    return QualityScore(
        overall_score=overall,
        completeness_score=comp_score,
        consistency_score=cons_score,
        issues=all_issues,
        grade=_letter_grade(overall),
    )
