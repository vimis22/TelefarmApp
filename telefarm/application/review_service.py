"""Use cases for en medicingennemgang: indsæt data, analysér, vælg fund, beslut og rapportér."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from telefarm.application.dto import RawClinicalData
from telefarm.application.errors import ReviewStateError
from telefarm.application.ports import (
    ClinicalDataImporter,
    ClinicalEngine,
    DemoDataSource,
    ReportRenderer,
)
from telefarm.domain.models import Decision, MedicationDecision, Report, Review


class ReviewService:
    def __init__(self, engine: ClinicalEngine, importer: ClinicalDataImporter,
                 renderer: ReportRenderer, demo_source: DemoDataSource,
                 clock: Callable[[], date] = date.today):
        self._engine = engine
        self._importer = importer
        self._renderer = renderer
        self._demo_source = demo_source
        self._clock = clock

    def demo_input(self) -> RawClinicalData:
        return self._demo_source.load()

    def import_data(self, review: Review, raw: RawClinicalData, is_demo: bool = False) -> list[str]:
        """Erstatter gennemgangens data og analyserer dem. Returnerer importadvarsler.

        Beslutninger, valgte fund og noter bevares for lægemidler og fund, der stadig findes.
        """
        result = self._importer.import_data(raw)
        review.patient = result.patient
        review.renal_function = result.renal_function
        review.medications = result.medications
        review.diagnoses = result.diagnoses
        review.dispensings = result.dispensings
        review.symptoms = result.symptoms
        review.is_demo = is_demo
        review.report = None

        medication_ids = {m.id for m in review.medications}
        review.medication_decisions = {
            med_id: decision for med_id, decision in review.medication_decisions.items()
            if med_id in medication_ids
        }
        review.analysis = None
        self.analyse(review)
        return result.warnings

    def analyse(self, review: Review) -> None:
        if not review.has_data:
            raise ReviewStateError("Indsæt patientdata, før der kan analyseres.")
        review.analysis = self._engine.analyse(review.to_clinical_input(self._clock()))
        valid_ids = {f.id for f in review.analysis.findings}
        review.selected_finding_ids &= valid_ids      # fjern fund der ikke findes mere
        review.finding_notes = {k: v for k, v in review.finding_notes.items() if k in valid_ids}

    def toggle_finding(self, review: Review, finding_id: str, selected: bool) -> None:
        if selected:
            review.selected_finding_ids.add(finding_id)
        else:
            review.selected_finding_ids.discard(finding_id)
        review.report = None

    def select_findings(self, review: Review, finding_ids: list[str]) -> None:
        review.selected_finding_ids |= set(finding_ids)
        review.report = None

    def clear_selection(self, review: Review) -> None:
        review.selected_finding_ids.clear()
        review.report = None

    def set_finding_note(self, review: Review, finding_id: str, note: str) -> None:
        note = note.strip()
        if note:
            review.finding_notes[finding_id] = note
        else:
            review.finding_notes.pop(finding_id, None)
        review.report = None

    def set_medication_decision(self, review: Review, medication_id: str,
                                decision: Decision, note: str | None = None) -> None:
        if review.medication(medication_id) is None:
            raise ReviewStateError(f"Ukendt lægemiddel: {medication_id}")
        current = review.decision_for(medication_id)
        review.medication_decisions[medication_id] = MedicationDecision(
            decision=decision,
            note=current.note if note is None else note.strip(),
        )
        review.report = None

    def apply_suggestion(self, review: Review, finding_id: str) -> None:
        """Bruger fundets foreslåede beslutning på de berørte lægemidler og medtager fundet."""
        finding = review.analysis.finding(finding_id) if review.analysis else None
        if finding is None:
            raise ReviewStateError("Fundet findes ikke længere – analysér igen.")
        for medication_id in finding.medication_ids:
            self.set_medication_decision(review, medication_id, finding.suggested_decision)
        self.toggle_finding(review, finding_id, selected=True)

    def generate_report(self, review: Review) -> Report:
        if not review.has_data or review.analysis is None:
            raise ReviewStateError("Der skal være en analyseret gennemgang, før rapporten kan dannes.")
        review.report = self._renderer.render(review, self._clock())
        return review.report
