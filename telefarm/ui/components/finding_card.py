"""Visning af kliniske fund med valg til rapport, note og "Brug forslag"."""

from __future__ import annotations

from collections.abc import Iterable

import streamlit as st

from telefarm.domain import labels
from telefarm.domain.models import Decision, Finding, Review
from telefarm.ui import labels as ui_labels
from telefarm.ui.dependencies import get_service


def finding_card(review: Review, finding: Finding, key_prefix: str, show_note: bool = True) -> None:
    """`key_prefix` skal være unik pr. sted, da samme fund kan vises flere gange på en side."""
    with st.container(border=True):
        st.markdown(
            f"{ui_labels.severity_badge(finding.severity)} {ui_labels.category_badge(finding.category)} "
            f"**{ui_labels.escape_markdown(finding.title)}**"
        )
        st.markdown(ui_labels.escape_markdown(finding.description))
        st.markdown(f"**Anbefaling:** {ui_labels.escape_markdown(finding.recommendation)}")

        names = review.medication_names(finding.medication_ids)
        details = [f"Forslag: **{labels.SUGGESTION[finding.suggested_decision]}**"]
        if names:
            details.append("Berører: " + ui_labels.escape_markdown(", ".join(names)))
        st.caption(" · ".join(details))

        _controls(review, finding, key_prefix)
        if show_note:
            _note(review, finding, key_prefix)


def findings_section(review: Review, findings: Iterable[Finding], key_prefix: str,
                     empty_text: str, show_note: bool = True) -> None:
    findings = list(findings)
    if not findings:
        st.success(empty_text, icon=":material/check_circle:")
        return
    for finding in findings:
        finding_card(review, finding, key_prefix, show_note)


def _controls(review: Review, finding: Finding, key_prefix: str) -> None:
    service = get_service()
    selected = finding.id in review.selected_finding_ids
    include_col, suggestion_col = st.columns([1, 1], vertical_alignment="center")

    # Valget indgår i nøglen, så alle kopier af fundet på siden altid viser samme tilstand.
    checkbox_key = f"{key_prefix}.select.{finding.id}.{int(selected)}"
    include_col.checkbox(
        "Medtag i rapport",
        value=selected,
        key=checkbox_key,
        on_change=lambda: service.toggle_finding(review, finding.id, st.session_state[checkbox_key]),
    )

    if finding.medication_ids and finding.suggested_decision is not Decision.UNDECIDED:
        already_applied = all(
            review.decision_for(med_id).decision == finding.suggested_decision
            for med_id in finding.medication_ids
        )
        suggestion_col.button(
            f"Brug forslag: {labels.DECISION[finding.suggested_decision]}",
            icon=":material/done_all:" if already_applied else ":material/bolt:",
            disabled=already_applied and selected,
            key=f"{key_prefix}.apply.{finding.id}",
            on_click=service.apply_suggestion,
            args=(review, finding.id),
        )


def _note(review: Review, finding: Finding, key_prefix: str) -> None:
    service = get_service()
    note_key = f"{key_prefix}.note.{finding.id}"
    st.text_area(
        "Klinisk note til rapporten",
        value=review.finding_notes.get(finding.id, ""),
        key=note_key,
        height=68,
        placeholder="Fx: Drøftet med patienten – ønsker udtrapning.",
        on_change=lambda: service.set_finding_note(review, finding.id, st.session_state[note_key]),
    )
