"""Diagnoser: patientens diagnoser og lægemidler der er uhensigtsmæssige ved dem."""

import streamlit as st

from telefarm.domain.models import FindingCategory
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import findings_section
from telefarm.ui.components.layout import page_frame
from telefarm.ui.routing import PageKey, WorkflowStep, go_to


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW, title="Diagnoser")

    if not review.diagnoses:
        empty_state(
            title="Ingen diagnoser",
            text="Indsæt patientens diagnoser fra journalen for at finde lægemiddel–sygdom-konflikter.",
            action_label="Indsæt diagnoser",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    st.dataframe(
        [{"Kode": d.code or "–", "Diagnose": d.text} for d in review.diagnoses],
        hide_index=True,
        width="stretch",
    )

    st.subheader("Lægemiddel–sygdom-konflikter")
    findings = review.analysis.findings_in(FindingCategory.DIAGNOSIS) if review.analysis else []
    findings_section(review, findings, "diagnoses",
                     "Ingen lægemidler er kontraindiceret ved de registrerede diagnoser.")
