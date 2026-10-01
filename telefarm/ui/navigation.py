"""Sidemenuen: sektionerne fra designet med markering af områder der har fund."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from telefarm.domain.models import Review
from telefarm.ui import routing
from telefarm.ui.routing import PageKey, PageSpec
from telefarm.ui.views import (
    adverse_effects,
    diagnoses,
    dispensings,
    insert_data,
    interactions,
    medication_list,
    patient_overview,
    renal_function,
    report_builder,
)

_RENDERERS: dict[PageKey, Callable[[], None]] = {
    PageKey.OVERVIEW: patient_overview.render,
    PageKey.INSERT: insert_data.render,
    PageKey.MEDICATIONS: medication_list.render,
    PageKey.DIAGNOSES: diagnoses.render,
    PageKey.INTERACTIONS: interactions.render,
    PageKey.DISPENSINGS: dispensings.render,
    PageKey.RENAL: renal_function.render,
    PageKey.ADVERSE_EFFECTS: adverse_effects.render,
    PageKey.REPORT: report_builder.render,
}


def build(review: Review) -> StreamlitPage:
    sections: dict[str, list[StreamlitPage]] = {}
    pages: dict[PageKey, StreamlitPage] = {}
    for spec in routing.PAGES:
        page = st.Page(
            _RENDERERS[spec.key],
            title=_title(spec, review),
            icon=spec.icon,
            url_path=spec.key.value,
            default=spec.key is PageKey.OVERVIEW,
        )
        pages[spec.key] = page
        sections.setdefault(spec.section, []).append(page)

    routing.register(pages)
    return st.navigation(sections)


def _title(spec: PageSpec, review: Review) -> str:
    if spec.key is PageKey.REPORT:
        count = len(review.selected_finding_ids)
        return f"{spec.title}  :gray-badge[{count}]" if count else spec.title
    if review.analysis and review.analysis.findings_in(*spec.categories):
        return f"{spec.title}  :green[●]"
    return spec.title
