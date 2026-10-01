"""Interaktioner og ACB: lægemiddelinteraktioner og samlet antikolinerg byrde."""

import streamlit as st

from telefarm.domain.models import FindingCategory, Review
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import findings_section
from telefarm.ui.components.layout import page_frame
from telefarm.ui.routing import PageKey, WorkflowStep, go_to


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW, title="Interaktioner og ACB")

    if review.analysis is None:
        empty_state(
            title="Ingen analyse",
            text="Indsæt og analysér medicinlisten for at se interaktioner og antikolinerg byrde.",
            action_label="Indsæt data",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    interactions_tab, acb_tab = st.tabs(["Interaktioner", "Antikolinerg byrde (ACB)"])
    with interactions_tab:
        findings_section(review, review.analysis.findings_in(FindingCategory.INTERACTION),
                         "interactions", "Ingen kendte interaktioner mellem de aktuelle lægemidler.")
    with acb_tab:
        _acb(review)


def _acb(review: Review) -> None:
    total = review.analysis.acb_total
    interpretation = (
        "Klinisk relevant byrde – øget risiko for kognitiv svækkelse og fald."
        if total >= 3 else "Under grænsen for klinisk relevant byrde (3)."
    )
    st.metric("Samlet ACB-score", total, help="Anticholinergic Cognitive Burden. Score ≥ 3 er klinisk relevant.")
    st.caption(interpretation)

    rows = [
        {"Lægemiddel": medication.display_name, "ATC": medication.atc,
         "ACB-score": review.analysis.acb_score_for(medication.id)}
        for medication in review.medications
        if review.analysis.acb_score_for(medication.id) > 0
    ]
    if rows:
        st.dataframe(sorted(rows, key=lambda r: -r["ACB-score"]), hide_index=True, width="stretch")

    findings_section(review, review.analysis.findings_in(FindingCategory.ACB), "acb",
                     "Den antikolinerge byrde giver ikke anledning til fund.")
