"""Composition root: det eneste sted hvor konkrete adaptere kobles på use cases."""

from __future__ import annotations

from telefarm.application.review_service import ReviewService
from telefarm.config import Settings
from telefarm.infrastructure.demo_data import DemoPatientSource
from telefarm.infrastructure.markdown_report import MarkdownReportRenderer
from telefarm.infrastructure.r_clinical_engine import RScriptClinicalEngine
from telefarm.infrastructure.text_importer import TextClinicalDataImporter


def build_review_service(settings: Settings | None = None) -> ReviewService:
    settings = settings or Settings.from_environment()
    return ReviewService(
        engine=RScriptClinicalEngine(
            rscript=settings.rscript_path,
            engine_script=settings.engine_script,
            timeout_seconds=settings.engine_timeout_seconds,
        ),
        importer=TextClinicalDataImporter(),
        renderer=MarkdownReportRenderer(),
        demo_source=DemoPatientSource(),
    )
