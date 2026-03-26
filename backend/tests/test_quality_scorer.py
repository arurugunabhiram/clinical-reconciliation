from core.quality_scorer import score_record_quality
from schemas.validate import PatientRecord, Severity


def test_complete_record_scores_high():
    record = PatientRecord(
        patient_id="P001",
        first_name="Jane",
        last_name="Doe",
        date_of_birth="1985-03-15",
        medications=[{"drug_name": "Lisinopril", "dose": "10mg"}],
        diagnoses=["Hypertension"],
        allergies=["Penicillin"],
    )
    result = score_record_quality(record)
    assert result.overall_score >= 0.85
    assert result.grade in ("A", "B")
    assert result.completeness_score == 1.0


def test_empty_record_scores_low():
    record = PatientRecord()
    result = score_record_quality(record)
    assert result.overall_score < 0.5
    assert result.grade in ("D", "F")
    assert any(i.severity == Severity.ERROR for i in result.issues)


def test_missing_medications_is_warning():
    record = PatientRecord(
        patient_id="P002",
        first_name="John",
        last_name="Smith",
        date_of_birth="1990-07-20",
    )
    result = score_record_quality(record)
    med_issues = [i for i in result.issues if i.field == "medications"]
    assert len(med_issues) == 1
    assert med_issues[0].severity == Severity.WARNING


def test_future_dob_flagged():
    record = PatientRecord(
        patient_id="P003",
        first_name="Test",
        last_name="Patient",
        date_of_birth="2099-01-01",
        medications=[{"drug_name": "Aspirin", "dose": "81mg"}],
        diagnoses=["None"],
        allergies=["NKDA"],
    )
    result = score_record_quality(record)
    dob_issues = [i for i in result.issues if i.field == "date_of_birth"]
    assert len(dob_issues) == 1
    assert dob_issues[0].severity == Severity.ERROR


def test_bad_date_format_flagged():
    record = PatientRecord(
        patient_id="P004",
        first_name="Test",
        last_name="Patient",
        date_of_birth="03/15/1985",
    )
    result = score_record_quality(record)
    dob_issues = [i for i in result.issues if i.field == "date_of_birth"]
    assert any("YYYY-MM-DD" in i.message for i in dob_issues)


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
    diag_issues = [i for i in result.issues if i.field == "diagnoses"]
    assert any("Duplicate" in i.message for i in diag_issues)


def test_incomplete_medication_entry():
    record = PatientRecord(
        patient_id="P006",
        first_name="Test",
        last_name="Patient",
        date_of_birth="1980-05-10",
        medications=[{"drug_name": "Lisinopril"}],  # missing dose
        diagnoses=["Hypertension"],
        allergies=["NKDA"],
    )
    result = score_record_quality(record)
    med_issues = [i for i in result.issues if "medications" in i.field]
    assert any("dose" in i.message for i in med_issues)
