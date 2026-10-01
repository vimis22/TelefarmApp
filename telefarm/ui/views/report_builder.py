"""Rapportbygger: vælg fund, skriv noter og dan den endelige rapport."""

from __future__ import annotations

import streamlit as st

from telefarm.domain import labels
from telefarm.domain.models import Review, Severity
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import finding_card
from telefarm.ui.components.layout import page_frame, run_safely
from telefarm.ui.dependencies import get_service
from telefarm.ui.routing import PageKey, WorkflowStep, go_to


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REPORT if review.report else WorkflowStep.SELECT,
               title="Rapportbygger")

    if review.analysis is None:
        empty_state(
            title="Intet at rapportere",
            text="Indsæt og analysér data, før fund kan vælges til rapporten.",
            action_label="Indsæt data",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    _selection_toolbar(review)
    for severity in Severity:
        findings = [f for f in review.findings if f.severity is severity]
        if findings:
            st.subheader(f"{labels.SEVERITY[severity]} alvorlighed ({len(findings)})")
            for finding in findings:
                finding_card(review, finding, key_prefix="report")

    _decisions_table(review)
    _report(review)


def _selection_toolbar(review: Review) -> None:
    service = get_service()
    high_ids = [f.id for f in review.findings if f.severity is Severity.HIGH]
    count_col, high_col, all_col, clear_col = st.columns([2, 1.2, 1, 1], vertical_alignment="center")
    count_col.markdown(f"**{len(review.selected_finding_ids)} af {len(review.findings)}** fund valgt")
    high_col.button("Vælg alle høje", on_click=service.select_findings, args=(review, high_ids),
                    disabled=not high_ids, width="stretch")
    all_col.button("Vælg alle", on_click=service.select_findings,
                   args=(review, [f.id for f in review.findings]), width="stretch")
    clear_col.button("Ryd valg", on_click=service.clear_selection, args=(review,),
                     disabled=not review.selected_finding_ids, width="stretch")


def _decisions_table(review: Review) -> None:
    st.subheader("Beslutninger pr. lægemiddel")
    st.caption("Beslutninger træffes på medicinlisten.")
    st.dataframe(
        [
            {"Lægemiddel": m.display_name,
             "Beslutning": labels.DECISION[review.decision_for(m.id).decision],
             "Note": review.decision_for(m.id).note}
            for m in review.medications
        ],
        hide_index=True,
        width="stretch",
    )
    if st.button("Gå til medicinlisten", icon=":material/pill:"):
        go_to(PageKey.MEDICATIONS)


def _report(review: Review) -> None:
    st.subheader("Rapport")
    if not review.selected_finding_ids:
        st.info("Vælg mindst ét fund for at medtage det i rapporten.", icon=":material/info:")

    if st.button("Generér rapport", type="primary", icon=":material/description:"):
        if run_safely(lambda: get_service().generate_report(review)):
            st.rerun()   # opdaterer trinindikatoren til "Generér rapport"

    if review.report is None:
        return
    with st.container(border=True):
        st.markdown(review.report.content)
    st.download_button(
        "Download rapport (Markdown)",
        data=review.report.content.encode("utf-8"),
        file_name=review.report.file_name,
        mime=review.report.mime_type,
        icon=":material/download:",
    )
