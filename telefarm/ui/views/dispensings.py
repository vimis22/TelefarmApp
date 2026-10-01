"""Apoteksudleveringer: adhærens og udleveringer der ikke matcher medicinlisten."""

from datetime import date

import streamlit as st

from telefarm.domain.models import FindingCategory, Review
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import findings_section
from telefarm.ui.components.layout import page_frame
from telefarm.ui.routing import PageKey, WorkflowStep, go_to


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW, title="Apoteksudleveringer")

    if not review.dispensings:
        empty_state(
            title="Ingen udleveringer",
            text="Indsæt apoteksudleveringer for at vurdere, om patienten henter sin medicin.",
            action_label="Indsæt udleveringer",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    st.subheader("Seneste udlevering pr. lægemiddel")
    st.dataframe(_last_dispensing_rows(review), hide_index=True, width="stretch",
                 column_config={"Dage siden": st.column_config.NumberColumn(format="%d")})

    with st.expander(f"Alle udleveringer ({len(review.dispensings)})"):
        st.dataframe(
            [{"Dato": d.dispensed_on.strftime("%d-%m-%Y"), "Præparat": d.name,
              "ATC": d.atc, "Pakninger": d.packages} for d in review.dispensings],
            hide_index=True, width="stretch",
        )

    st.subheader("Adhærens")
    findings = review.analysis.findings_in(FindingCategory.ADHERENCE) if review.analysis else []
    findings_section(review, findings, "dispensings",
                     "Udleveringerne stemmer overens med medicinlisten.")


def _last_dispensing_rows(review: Review) -> list[dict]:
    today = date.today()
    rows = []
    for medication in review.medications:
        last = review.last_dispensing_for(medication)
        rows.append({
            "Lægemiddel": medication.display_name,
            "Seneste udlevering": last.dispensed_on.strftime("%d-%m-%Y") if last else "Ingen",
            "Dage siden": (today - last.dispensed_on).days if last else None,
        })
    return rows
