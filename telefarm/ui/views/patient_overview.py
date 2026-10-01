"""Patientoverblik: nøgletal, fund pr. område og de mest alvorlige fund."""

from __future__ import annotations

from collections import Counter

import streamlit as st

from telefarm.domain import labels
from telefarm.domain.models import Review, Severity
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import finding_card
from telefarm.ui.components.layout import page_frame, run_safely
from telefarm.ui.dependencies import get_service
from telefarm.ui.routing import REVIEW_PAGES, PageKey, WorkflowStep, go_to

_TOP_FINDINGS = 5


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW if review.has_data else WorkflowStep.INSERT,
               title="Patientoverblik")

    if not review.has_data:
        empty_state(
            title="Ingen patient",
            text="Indsæt data fra FMK, eller indlæs den fiktive demo-patient for at komme i gang.",
            action_label="Indsæt data",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    _key_figures(review)
    if review.analysis is None:
        st.warning("Data er ikke analyseret endnu.", icon=":material/warning:")
        if st.button("Analysér", type="primary", icon=":material/play_arrow:"):
            if run_safely(lambda: get_service().analyse(review)):
                st.rerun()
        return

    _severity_figures(review)
    _areas(review)
    _top_findings(review)

    if st.button("Kør analysen igen", icon=":material/refresh:"):
        if run_safely(lambda: get_service().analyse(review)):
            state.flash("Analysen er kørt igen.")
            st.rerun()


def _key_figures(review: Review) -> None:
    patient = review.patient
    egfr = review.analysis.egfr if review.analysis else None
    columns = st.columns(4)
    columns[0].metric("Patient", f"{patient.age} år", labels.SEX[patient.sex], delta_color="off", delta_arrow="off")
    columns[1].metric("Lægemidler", len(review.medications))
    columns[2].metric("eGFR", f"{egfr.value:.0f}" if egfr else "–",
                      egfr.ckd_stage if egfr else None, delta_color="off", delta_arrow="off")
    columns[3].metric("ACB-score", review.analysis.acb_total if review.analysis else "–")


def _severity_figures(review: Review) -> None:
    counts = Counter(f.severity for f in review.findings)
    st.subheader(f"{len(review.findings)} fund")
    for column, severity in zip(st.columns(3), Severity):
        column.metric(labels.SEVERITY[severity], counts.get(severity, 0))


def _areas(review: Review) -> None:
    st.subheader("Fund pr. område")
    for page in REVIEW_PAGES:
        findings = review.analysis.findings_in(*page.categories)
        high = sum(1 for f in findings if f.severity is Severity.HIGH)
        with st.container(border=True):
            name_col, count_col, action_col = st.columns([3, 2, 1], vertical_alignment="center")
            name_col.markdown(f"{page.icon} **{page.title}**")
            summary = f"{len(findings)} fund" + (f" · :red-badge[{high} høj]" if high else "")
            count_col.markdown(summary if findings else ":green-badge[Ingen fund]")
            if action_col.button("Åbn", key=f"overview.open.{page.key}", width="stretch"):
                go_to(page.key)


def _top_findings(review: Review) -> None:
    top = [f for f in review.findings if f.severity is Severity.HIGH][:_TOP_FINDINGS]
    if not top:
        return
    st.subheader("Mest alvorlige fund")
    for finding in top:
        finding_card(review, finding, key_prefix="overview", show_note=False)
