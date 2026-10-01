from datetime import date

import pytest

from telefarm.application.dto import RawClinicalData
from telefarm.application.errors import ImportValidationError
from telefarm.domain.models import Sex
from telefarm.infrastructure.text_importer import TextClinicalDataImporter, parse_date, parse_symptoms

PATIENT = dict(patient_pseudonym="TF-001", age=80, sex="female")


def import_data(**fields):
    return TextClinicalDataImporter().import_data(RawClinicalData(**{**PATIENT, **fields}))


def test_parses_semicolon_and_tab_separated_medications_and_skips_header():
    result = import_data(medications_text=(
        "Lægemiddel; ATC; Styrke; Dosering; Indikation\n"
        "Metformin; A10BA02; 500 mg; 1 x 3; Diabetes\n"
        "Digoxin\tC01AA05\t62,5 mikrogram\t1 x 1\tAtrieflimren\n"
    ))
    assert [m.name for m in result.medications] == ["Metformin", "Digoxin"]
    assert result.medications[1].strength == "62,5 mikrogram"
    assert result.warnings == []


def test_medication_ids_are_stable_across_imports_and_unique_for_duplicates():
    text = "Metformin; A10BA02; 500 mg\nMetformin; A10BA02; 500 mg"
    first, second = import_data(medications_text=text), import_data(medications_text=text)
    assert [m.id for m in first.medications] == [m.id for m in second.medications]
    assert len({m.id for m in first.medications}) == 2


def test_invalid_or_missing_atc_gives_warning():
    result = import_data(medications_text="Ukendt\nNoget; XYZ")
    assert len(result.warnings) == 2
    assert all(m.atc == "" for m in result.medications)


def test_patient_is_validated():
    with pytest.raises(ImportValidationError):
        TextClinicalDataImporter().import_data(RawClinicalData(age=80, sex="female"))
    with pytest.raises(ImportValidationError, match="CPR"):
        import_data(patient_pseudonym="010203-1234")
    with pytest.raises(ImportValidationError):
        import_data(sex="")


def test_sex_accepts_danish_labels():
    assert import_data(sex="Mand").patient.sex is Sex.MALE


def test_dispensings_are_parsed_sorted_and_invalid_lines_reported():
    result = import_data(dispensings_text="01-02-2026; Metformin; A10BA02; 2\n2026-05-01; Digoxin\nikke en dato; X")
    assert [d.dispensed_on for d in result.dispensings] == [date(2026, 5, 1), date(2026, 2, 1)]
    assert result.dispensings[1].packages == 2
    assert len(result.warnings) == 1


def test_zero_lab_values_are_treated_as_missing():
    result = import_data(creatinine_umol_l=0.0, egfr_reported=None)
    assert result.renal_function.creatinine_umol_l is None


def test_parse_symptoms_normalises_and_deduplicates():
    assert parse_symptoms("Svimmelhed, mundtørhed;svimmelhed\n") == ["svimmelhed", "mundtørhed"]


@pytest.mark.parametrize("text", ["2026-10-01", "01-10-2026", "01.10.2026", "01/10/2026"])
def test_parse_date_formats(text):
    assert parse_date(text) == date(2026, 10, 1)
