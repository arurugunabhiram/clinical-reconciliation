from core.quality_scorer import score_record_quality
from schemas.validate import PatientRecord, IssueSeverity


def test_complete_record_scores_high():
    record = PatientRecord(
        patient_id="P001",
        first_name="Jane",
        last_name="Doe",
        date_of_birth="1985-03-15",
        medications=[{"drug_name": "Lisinopril", "dose": "10mg"}],
        diagnoses=["Hypertension"],
        allergies=["Penicillin"],
        vital_signs={"blood_pressure": "120/80", "heart_rate": 72},
        last_updated="2026-03-20",
    )
    result = score_record_quality(record)
    assert result.overall_score >= 85
    assert result.grade in ("A", "B")
    assert result.breakdown.completeness == 100


def test_empty_record_scores_low():
    record = PatientRecord()
    result = score_record_quality(record)
    assert result.breakdown.completeness == 0
    assert result.overall_score <= 65  # accuracy/plausibility stay high with no data to check
    assert result.grade in ("D", "F")
    assert any(i.severity == IssueSeverity.HIGH for i in result.issues_detected)


def test_missing_medications_is_medium():
    record = PatientRecord(
        patient_id="P002",
        first_name="John",
        last_name="Smith",
        date_of_birth="1990-07-20",
    )
    result = score_record_quality(record)
    med_issues = [i for i in result.issues_detected if i.field == "medications"]
    assert len(med_issues) == 1
    assert med_issues[0].severity == IssueSeverity.MEDIUM


def test_future_dob_flagged():
    record = PatientRecord(
        patient_id="P003",
        first_name="Test",
        last_name="Patient",
        date_of_birth="2099-01-01",
        medications=[{"drug_name": "Aspirin", "dose": "81mg"}],
        diagnoses=["None"],
        allergies=["NKDA"],
        vital_signs={"heart_rate": 72},
        last_updated="2026-03-20",
    )
    result = score_record_quality(record)
    dob_issues = [i for i in result.issues_detected if i.field == "date_of_birth"]
    assert len(dob_issues) == 1
    assert dob_issues[0].severity == IssueSeverity.HIGH


def test_bad_date_format_flagged():
    record = PatientRecord(
        patient_id="P004",
        first_name="Test",
        last_name="Patient",
        date_of_birth="03/15/1985",
    )
    result = score_record_quality(record)
    dob_issues = [i for i in result.issues_detected if i.field == "date_of_birth"]
    assert any("YYYY-MM-DD" in i.issue for i in dob_issues)


def test_duplicate_diagnoses_flagged():
    record = PatientRecord(
        patient_id="P005",
        first_name="Test",
        last_name="Patient",
        date_of_birth="1970-01-01",
        medications=[{"drug_name": "Metformin", "dose": "500mg"}],
        diagnoses=["Diabetes", "diabetes"],
        allergies=["Sulfa"],
    )
    result = score_record_quality(record)
    diag_issues = [i for i in result.issues_detected if i.field == "diagnoses"]
    assert any("Duplicate" in i.issue for i in diag_issues)


def test_impossible_blood_pressure_flagged():
    record = PatientRecord(
        patient_id="P007",
        first_name="Test",
        last_name="Patient",
        date_of_birth="1955-03-15",
        medications=[{"drug_name": "Lisinopril", "dose": "10mg"}],
        diagnoses=["Hypertension"],
        vital_signs={"blood_pressure": "340/180", "heart_rate": 72},
        last_updated="2026-03-20",
    )
    result = score_record_quality(record)
    bp_issues = [i for i in result.issues_detected if "blood_pressure" in i.field]
    assert len(bp_issues) >= 1
    assert any(i.severity == IssueSeverity.HIGH for i in bp_issues)
    assert result.breakdown.clinical_plausibility < 80


def test_timeliness_old_record_penalized():
    record = PatientRecord(
        patient_id="P008",
        first_name="Test",
        last_name="Patient",
        date_of_birth="1960-01-01",
        medications=[{"drug_name": "Aspirin", "dose": "81mg"}],
        diagnoses=["CAD"],
        allergies=["NKDA"],
        vital_signs={"heart_rate": 68},
        last_updated="2024-06-15",
    )
    result = score_record_quality(record)
    assert result.breakdown.timeliness <= 50


def test_metformin_low_egfr_contraindication():
    record = PatientRecord(
        patient_id="P009",
        first_name="Test",
        last_name="Patient",
        date_of_birth="1950-05-10",
        medications=[{"drug_name": "Metformin", "dose": "1000mg"}],
        diagnoses=["Type 2 Diabetes", "CKD Stage 4"],
        lab_results={"eGFR": "25 mL/min"},
        vital_signs={"blood_pressure": "140/90"},
        last_updated="2026-03-20",
    )
    result = score_record_quality(record)
    contra_issues = [i for i in result.issues_detected if "contraindicated" in i.issue.lower()]
    assert len(contra_issues) >= 1
    assert contra_issues[0].severity == IssueSeverity.HIGH


def test_four_dimension_breakdown_present():
    record = PatientRecord(patient_id="P010")
    result = score_record_quality(record)
    assert hasattr(result, "breakdown")
    assert hasattr(result.breakdown, "completeness")
    assert hasattr(result.breakdown, "accuracy")
    assert hasattr(result.breakdown, "timeliness")
    assert hasattr(result.breakdown, "clinical_plausibility")
    assert result.overall_score == round(
        result.breakdown.completeness * 0.25
        + result.breakdown.accuracy * 0.25
        + result.breakdown.timeliness * 0.25
        + result.breakdown.clinical_plausibility * 0.25
    )
