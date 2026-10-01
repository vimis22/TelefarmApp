"""Bivirkninger: patientens symptomer koblet til mulige årsagspræparater."""

import streamlit as st

from telefarm.domain.models import FindingCategory
from telefarm.ui import labels as ui_labels
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import findings_section
from telefarm.ui.components.layout import page_frame
from telefarm.ui.routing import PageKey, WorkflowStep, go_to


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW, title="Bivirkninger")

    if not review.symptoms:
        empty_state(
            title="Ingen symptomer registreret",
            text="Angiv patientens symptomer (fx svimmelhed, obstipation) for at finde mulige bivirkninger.",
            action_label="Tilføj symptomer",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    st.markdown("**Symptomer:** " + " ".join(
        f":gray-badge[{ui_labels.escape_markdown(symptom)}]" for symptom in review.symptoms
    ))
    findings = review.analysis.findings_in(FindingCategory.ADVERSE_EFFECT) if review.analysis else []
    findings_section(review, findings, "adverse_effects",
                     "Ingen af symptomerne er kendte bivirkninger ved de aktuelle lægemidler.")
