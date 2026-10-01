"""Use cases testes med falske adaptere – R er ikke nødvendig."""

from datetime import date

import pytest

from telefarm.application.dto import RawClinicalData
from telefarm.application.errors import ReviewStateError
from telefarm.application.review_service import ReviewService
from telefarm.domain.models import (
    AnalysisResult,
    ClinicalInput,
    Decision,
    Finding,
    FindingCategory,
    Review,
    Severity,
)
from telefarm.infrastructure.markdown_report import MarkdownReportRenderer
from telefarm.infrastructure.text_importer import TextClinicalDataImporter

TODAY = date(2026, 10, 1)
RAW = RawClinicalData(
    patient_pseudonym="TF-001", age=80, sex="female",
    medications_text="Ibuprofen; M01AE01; 400 mg; 1 x 3; Smerter\nApixaban; B01AF02; 5 mg; 1 x 2; AF",
)


class FakeEngine:
    """Returnerer ét interaktionsfund for de to første lægemidler."""

    def __init__(self):
        self.received: ClinicalInput | None = None

    def analyse(self, clinical_input: ClinicalInput) -> AnalysisResult:
        self.received = clinical_input
        ids = tuple(m.id for m in clinical_input.medications[:2])
        finding = Finding(
            id="interaction:test", category=FindingCategory.INTERACTION, severity=Severity.HIGH,
            title="Ibuprofen + Apixaban", description="Blødning", recommendation="Undgå",
            suggested_decision=Decision.STOP, medication_ids=ids,
        )
        return AnalysisResult(egfr=None, acb_items=(), findings=(finding,) if len(ids) == 2 else ())


class FakeDemoSource:
    def load(self) -> RawClinicalData:
        return RAW


@pytest.fixture
def engine():
    return FakeEngine()


@pytest.fixture
def service(engine):
    return ReviewService(engine, TextClinicalDataImporter(), MarkdownReportRenderer(),
                         FakeDemoSource(), clock=lambda: TODAY)


@pytest.fixture
def review(service):
    review = Review()
    service.import_data(review, RAW)
    return review


def test_import_analyses_with_reference_date(review, engine):
    assert engine.received.reference_date == TODAY
    assert len(review.findings) == 1


def test_analyse_requires_data(service):
    with pytest.raises(ReviewStateError):
        service.analyse(Review())


def test_apply_suggestion_sets_decisions_and_selects_finding(service, review):
    service.apply_suggestion(review, "interaction:test")
    assert review.selected_finding_ids == {"interaction:test"}
    assert {review.decision_for(m.id).decision for m in review.medications} == {Decision.STOP}


def test_reimport_keeps_decisions_for_remaining_medications(service, review):
    ibuprofen = review.medications[0]
    service.set_medication_decision(review, ibuprofen.id, Decision.STOP, note="Seponeres")
    service.toggle_finding(review, "interaction:test", True)

    service.import_data(review, RawClinicalData(**{**RAW.__dict__,
                                                   "medications_text": "Ibuprofen; M01AE01; 400 mg"}))

    assert review.decision_for(ibuprofen.id).note == "Seponeres"
    assert review.selected_finding_ids == set()       # fundet findes ikke længere


def test_changes_invalidate_generated_report(service, review):
    service.generate_report(review)
    assert review.report is not None
    service.toggle_finding(review, "interaction:test", True)
    assert review.report is None


def test_report_contains_selected_findings_notes_and_decisions(service, review):
    service.apply_suggestion(review, "interaction:test")
    service.set_finding_note(review, "interaction:test", "Drøftet med patient")
    report = service.generate_report(review)
    assert report.file_name == "medicingennemgang_TF-001_2026-10-01.md"
    assert "Ibuprofen + Apixaban" in report.content
    assert "Drøftet med patient" in report.content
    assert "| Seponér |" in report.content


def test_set_decision_for_unknown_medication_fails(service, review):
    with pytest.raises(ReviewStateError):
        service.set_medication_decision(review, "findes-ikke", Decision.STOP)


def test_suggested_decision_prefers_most_severe_concrete_suggestion(review):
    assert review.analysis.suggested_decision_for(review.medications[0].id) is Decision.STOP
