"""Integrationstest mod den rigtige R-regelmotor. Springes over, hvis R ikke er installeret."""

from datetime import date

import pytest

from telefarm.application.errors import ClinicalEngineError
from telefarm.config import Settings
from telefarm.domain.models import (
    ClinicalInput,
    Diagnosis,
    EgfrSource,
    FindingCategory,
    Medication,
    Patient,
    RenalFunction,
    Sex,
)
from telefarm.infrastructure.r_clinical_engine import RScriptClinicalEngine

settings = Settings.from_environment()
pytestmark = pytest.mark.skipif(settings.rscript_path is None, reason="Rscript er ikke installeret")


@pytest.fixture(scope="module")
def engine():
    return RScriptClinicalEngine(settings.rscript_path, settings.engine_script)


def clinical_input(**overrides) -> ClinicalInput:
    values = dict(
        patient=Patient(pseudonym="TF-001", age=78, sex=Sex.FEMALE),
        medications=(
            Medication(id="m1", name="Ibuprofen", atc="M01AE01", indication="Smerter"),
            Medication(id="m2", name="Apixaban", atc="B01AF02", indication="AF"),
            Medication(id="m3", name="Amitriptylin", atc="N06AA09", indication="Neuropati"),
        ),
        diagnoses=(Diagnosis(code="DI50.9", text="Hjertesvigt"),),
        dispensings=(),
        symptoms=("mundtørhed",),
        renal_function=RenalFunction(creatinine_umol_l=125),
        reference_date=date(2026, 10, 1),
    )
    return ClinicalInput(**{**values, **overrides})


def test_engine_returns_domain_result(engine):
    result = engine.analyse(clinical_input())

    assert result.egfr.value == 38
    assert result.egfr.source is EgfrSource.CKD_EPI_2021
    assert result.acb_total == 3
    categories = {f.category for f in result.findings}
    assert {FindingCategory.RENAL, FindingCategory.INTERACTION, FindingCategory.DIAGNOSIS,
            FindingCategory.ACB, FindingCategory.ADVERSE_EFFECT} <= categories


def test_danish_characters_survive_the_round_trip(engine):
    result = engine.analyse(clinical_input())
    assert any("ø" in f.title or "æ" in f.description for f in result.findings)


def test_empty_medication_list_gives_no_findings(engine):
    result = engine.analyse(clinical_input(medications=(), symptoms=()))
    assert result.findings == ()


def test_missing_rscript_raises_clear_error():
    with pytest.raises(ClinicalEngineError, match="TELEFARM_RSCRIPT"):
        RScriptClinicalEngine(None, settings.engine_script).analyse(clinical_input())
