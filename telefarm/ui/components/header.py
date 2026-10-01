"""Topbjælke: afsender, aktuel patient, nøgletal og genvej til rapporten."""

from __future__ import annotations

from collections.abc import Callable
from html import escape

import streamlit as st

from telefarm.domain.models import Review


def render(review: Review, on_new_review: Callable[[], None], on_open_report: Callable[[], None]) -> None:
    brand, action = st.columns([5, 1.4], vertical_alignment="center")
    with brand:
        st.html(
            '<div class="tf-brand">'
            '<div class="tf-brand__region">Region<br>Syddanmark</div>'
            '<div><div class="tf-brand__title">Telefarmakologisk Ambulatorium</div>'
            '<div class="tf-brand__subtitle">OUH · Klinisk Farmakologi</div></div>'
            "</div>"
        )
    with action:
        if st.button("Ny gennemgang", icon=":material/add:", type="tertiary", key="header.new"):
            on_new_review()

    st.html('<hr class="tf-rule">')
    _patient_bar(review, on_open_report)
    st.html('<hr class="tf-rule">')


def _patient_bar(review: Review, on_open_report: Callable[[], None]) -> None:
    patient_col, medicine_col, renal_col, report_col = st.columns(
        [4, 1.4, 2.1, 1.3], vertical_alignment="center"
    )
    with patient_col:
        if review.patient:
            name = (f'Patient {escape(review.patient.pseudonym)}'
                    f'<span class="tf-muted"> · {review.patient.age} år</span>')
        else:
            name = '<span class="tf-muted">Ingen patient indlæst</span>'
        st.html(f'<div class="tf-eyebrow">Aktuel gennemgang</div><div class="tf-patient">{name}</div>')

    if review.patient is None:
        return

    with medicine_col:
        st.html(_key_figure("Medicin", f"{len(review.medications)} lægemidler"))
    with renal_col:
        egfr = review.analysis.egfr if review.analysis else None
        value = (f'eGFR {egfr.value:.0f} <span class="tf-unit">mL/min/1,73 m²</span>'
                 if egfr else '<span class="tf-muted">Ikke oplyst</span>')
        st.html(_key_figure("Nyrefunktion", value))
    with report_col:
        count = len(review.selected_finding_ids)
        if st.button(f"Rapport  **{count}**", icon=":material/description:", type="primary",
                     width="stretch", key="header.report"):
            on_open_report()


def _key_figure(label: str, value_html: str) -> str:
    return (f'<div class="tf-figure"><div class="tf-figure__label">{label}</div>'
            f'<div class="tf-figure__value">{value_html}</div></div>')
