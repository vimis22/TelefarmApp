"""Porte (interfaces) som infrastrukturen implementerer.

Use cases afhænger kun af disse protokoller – aldrig af R, filer eller Streamlit.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from telefarm.application.dto import ImportResult, RawClinicalData
from telefarm.domain.models import AnalysisResult, ClinicalInput, Report, Review


class ClinicalEngine(Protocol):
    def analyse(self, clinical_input: ClinicalInput) -> AnalysisResult: ...


class ClinicalDataImporter(Protocol):
    def import_data(self, raw: RawClinicalData) -> ImportResult: ...


class ReportRenderer(Protocol):
    def render(self, review: Review, generated_on: date) -> Report: ...


class DemoDataSource(Protocol):
    def load(self) -> RawClinicalData: ...
