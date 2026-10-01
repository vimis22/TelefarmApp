"""Nyrefunktion: eGFR, CKD-stadie og lægemidler der skal dosisjusteres."""

import streamlit as st

from telefarm.domain import labels
from telefarm.domain.models import FindingCategory
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import findings_section
from telefarm.ui.components.layout import page_frame
from telefarm.ui.routing import PageKey, WorkflowStep, go_to

_STAGE_TEXT = {
    "G1": "Normal eller høj",
    "G2": "Let nedsat",
    "G3a": "Let til moderat nedsat",
    "G3b": "Moderat til svært nedsat",
    "G4": "Svært nedsat",
    "G5": "Nyresvigt",
}


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW, title="Nyrefunktion")

    if review.analysis is None:
        empty_state(
            title="Ingen nyrefunktion",
            text="Indsæt P-kreatinin eller eGFR sammen med medicinlisten.",
            action_label="Indsæt data",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    egfr = review.analysis.egfr
    creatinine = review.renal_function.creatinine_umol_l
    creatinine_col, egfr_col, stage_col = st.columns(3)
    creatinine_col.metric("P-kreatinin", f"{creatinine:.0f} µmol/L" if creatinine else "–")
    egfr_col.metric("eGFR", f"{egfr.value:.0f} mL/min/1,73 m²" if egfr else "–",
                    labels.EGFR_SOURCE[egfr.source] if egfr else None, delta_color="off", delta_arrow="off")
    stage_col.metric("CKD-stadie", egfr.ckd_stage if egfr else "–",
                     _STAGE_TEXT[egfr.ckd_stage] if egfr else None, delta_color="off", delta_arrow="off")

    if egfr is None:
        st.info("Nyrefunktionen er ikke oplyst – renal dosering kan ikke vurderes.",
                icon=":material/info:")

    st.subheader("Lægemidler med renal dosering")
    findings_section(review, review.analysis.findings_in(FindingCategory.RENAL), "renal",
                     "Ingen lægemidler kræver dosisjustering ved den aktuelle nyrefunktion.")
