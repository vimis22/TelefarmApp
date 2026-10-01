"""Medicinliste: hvert lægemiddel med fund, ACB-score og klinisk beslutning."""

from __future__ import annotations

from collections import Counter

import streamlit as st

from telefarm.domain import labels
from telefarm.domain.models import Decision, FindingCategory, Medication, Review, Severity
from telefarm.ui import labels as ui_labels
from telefarm.ui import state
from telefarm.ui.components.empty_state import empty_state
from telefarm.ui.components.finding_card import finding_card, findings_section
from telefarm.ui.components.layout import page_frame
from telefarm.ui.dependencies import get_service
from telefarm.ui.routing import PageKey, WorkflowStep, go_to


def render() -> None:
    review = state.get_review()
    page_frame(step=WorkflowStep.REVIEW, title="Medicinliste")

    if not review.medications:
        empty_state(
            title="Ingen medicinliste",
            text="Indsæt aktuelle ordinationer fra FMK for at oprette medicinlisten.",
            action_label="Indsæt ordinationer",
            on_action=lambda: go_to(PageKey.INSERT),
        )
        return

    _decision_summary(review)
    if review.analysis:
        general = review.analysis.findings_in(FindingCategory.INDICATION)
        with st.expander(f"Fund om indikation og polyfarmaci ({len(general)})", expanded=False):
            findings_section(review, general, "medications.general",
                             "Alle lægemidler har en angivet indikation.", show_note=False)

    for medication in review.medications:
        _render_medication_row(review, medication)   # badges + Fortsæt/Justér/Seponér


def _decision_summary(review: Review) -> None:
    counts = Counter(review.decision_for(m.id).decision for m in review.medications)
    columns = st.columns(len(Decision))
    for column, decision in zip(columns, (Decision.UNDECIDED, *ui_labels.DECISION_OPTIONS)):
        column.metric(labels.DECISION[decision], counts.get(decision, 0))


def _render_medication_row(review: Review, medication: Medication) -> None:
    analysis = review.analysis
    findings = analysis.findings_for_medication(medication.id) if analysis else []

    with st.container(border=True):
        info_col, decision_col = st.columns([3, 2])
        with info_col:
            atc = f"`{medication.atc}`" if medication.atc else ":orange-badge[ATC mangler]"
            st.markdown(f"**{ui_labels.escape_markdown(medication.display_name)}** {atc}")
            st.caption(
                f"{ui_labels.escape_markdown(medication.dosage or 'Dosering ikke angivet')} · "
                f"Indikation: {ui_labels.escape_markdown(medication.indication or 'ikke angivet')}"
            )
            badges = _finding_badges(findings)
            acb = analysis.acb_score_for(medication.id) if analysis else 0
            if acb:
                badges.append(f":violet-badge[ACB {acb}]")
            st.markdown(" ".join(badges) if badges else ":green-badge[Ingen fund]")

        with decision_col:
            _decision_control(review, medication)

        if findings:
            with st.expander(f"Vis {len(findings)} fund"):
                for finding in findings:
                    finding_card(review, finding, key_prefix=f"medications.{medication.id}",
                                 show_note=False)


def _finding_badges(findings) -> list[str]:
    counts = Counter(f.severity for f in findings)
    return [
        f":{ui_labels.SEVERITY_COLOR[severity]}-badge[{counts[severity]} {labels.SEVERITY[severity].lower()}]"
        for severity in Severity if counts[severity]
    ]


def _decision_control(review: Review, medication: Medication) -> None:
    service = get_service()
    current = review.decision_for(medication.id)
    # Beslutningen indgår i nøglen, så kontrollen følger med, når "Brug forslag" ændrer den.
    decision_key = f"medications.decision.{medication.id}.{current.decision.value}"
    st.segmented_control(
        "Beslutning",
        options=ui_labels.DECISION_OPTIONS,
        format_func=labels.DECISION.get,
        default=None if current.decision is Decision.UNDECIDED else current.decision,
        key=decision_key,
        label_visibility="collapsed",
        on_change=lambda: service.set_medication_decision(
            review, medication.id, st.session_state[decision_key] or Decision.UNDECIDED
        ),
    )

    if review.analysis:
        suggestion = review.analysis.suggested_decision_for(medication.id)
        if suggestion is not Decision.UNDECIDED and suggestion != current.decision:
            st.caption(f"Systemets forslag: **{labels.DECISION[suggestion]}**")

    note_key = f"medications.note.{medication.id}"
    st.text_input(
        "Note",
        value=current.note,
        key=note_key,
        placeholder="Note til beslutningen, fx ny dosis",
        label_visibility="collapsed",
        on_change=lambda: service.set_medication_decision(
            review, medication.id, review.decision_for(medication.id).decision,
            note=st.session_state[note_key],
        ),
    )
