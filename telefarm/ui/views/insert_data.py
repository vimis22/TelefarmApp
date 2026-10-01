"""Indsæt data: patientoplysninger og tekst kopieret fra FMK, journal og apotek."""

from __future__ import annotations

import streamlit as st

from telefarm.application.dto import RawClinicalData
from telefarm.application.errors import ClinicalEngineError, TelefarmError
from telefarm.domain import labels
from telefarm.domain.models import Sex
from telefarm.ui import state
from telefarm.ui.components.layout import page_frame
from telefarm.ui.dependencies import get_service
from telefarm.ui.routing import PageKey, WorkflowStep, go_to

_MEDICATION_HELP = "Én ordination pr. linje: Lægemiddel; ATC; Styrke; Dosering; Indikation"
_DIAGNOSIS_HELP = "Én diagnose pr. linje: Kode; Diagnose (SKS eller ICD-10)"
_DISPENSING_HELP = "Én udlevering pr. linje: Dato; Præparat; ATC; Pakninger"


def render() -> None:
    page_frame(
        step=WorkflowStep.INSERT,
        title="Indsæt data",
        caption="Kopiér fra FMK, journal og apotekssystem. Kolonner adskilles med tabulator, ; eller |.",
    )
    _import_warnings()
    _demo_button()
    _data_form(state.get_raw_input(), state.form_version())


def _import_warnings() -> None:
    warnings = state.get_import_warnings()
    if not warnings:
        return
    with st.container(border=True):
        st.warning(f"Data er indsat med {len(warnings)} advarsel(er):", icon=":material/warning:")
        for warning in warnings:
            st.markdown(f"- {warning}")
        if st.button("Fortsæt til medicinlisten", icon=":material/arrow_forward:"):
            state.set_import_warnings([])
            go_to(PageKey.MEDICATIONS)


def _demo_button() -> None:
    if st.button("Indlæs fiktiv demo-patient TF-024", icon=":material/science:"):
        raw = get_service().demo_input()
        state.set_raw_input(raw, refresh_form=True)
        _import(raw, is_demo=True)


def _data_form(raw: RawClinicalData, version: int) -> None:
    def key(name: str) -> str:
        return f"insert.{name}.{version}"

    with st.form(key=f"insert.form.{version}", border=True):
        st.subheader("Patient")
        pseudonym_col, age_col, sex_col, weight_col = st.columns(4)
        pseudonym = pseudonym_col.text_input("Pseudonym", value=raw.patient_pseudonym,
                                             placeholder="TF-024", key=key("pseudonym"),
                                             help="Brug aldrig CPR-nummer.")
        age = age_col.number_input("Alder (år)", min_value=0, max_value=130, value=raw.age,
                                   step=1, key=key("age"))
        sex_options = list(Sex)
        sex = sex_col.selectbox("Køn", sex_options, format_func=labels.SEX.get, key=key("sex"),
                                index=sex_options.index(Sex(raw.sex)) if raw.sex else None,
                                placeholder="Vælg")
        weight = weight_col.number_input("Vægt (kg)", min_value=0.0, max_value=400.0,
                                         value=_as_float(raw.weight_kg), key=key("weight"))

        st.subheader("Nyrefunktion")
        creatinine_col, egfr_col = st.columns(2)
        creatinine = creatinine_col.number_input(
            "P-kreatinin (µmol/L)", min_value=0.0, max_value=3000.0,
            value=_as_float(raw.creatinine_umol_l), key=key("creatinine"),
            help="eGFR beregnes med CKD-EPI 2021, hvis den ikke er oplyst.",
        )
        egfr = egfr_col.number_input(
            "eGFR (mL/min/1,73 m²) – valgfri", min_value=0.0, max_value=200.0,
            value=_as_float(raw.egfr_reported), key=key("egfr"),
            help="Udfyld kun hvis laboratoriets eGFR skal bruges i stedet for beregningen.",
        )

        st.subheader("Kliniske data")
        medications = st.text_area("Aktuelle ordinationer (FMK)", value=raw.medications_text,
                                   height=220, key=key("medications"), help=_MEDICATION_HELP,
                                   placeholder="Metformin; A10BA02; 500 mg; 1 x 3 dagligt; Type 2-diabetes")
        diagnoses = st.text_area("Diagnoser", value=raw.diagnoses_text, height=140,
                                 key=key("diagnoses"), help=_DIAGNOSIS_HELP,
                                 placeholder="DI50.9; Hjertesvigt")
        dispensings = st.text_area("Apoteksudleveringer", value=raw.dispensings_text, height=140,
                                   key=key("dispensings"), help=_DISPENSING_HELP,
                                   placeholder="12-08-2026; Metformin; A10BA02; 1")
        symptoms = st.text_input("Symptomer (kommasepareret)", value=raw.symptoms_text,
                                 key=key("symptoms"), placeholder="svimmelhed, mundtørhed")

        if st.form_submit_button("Gem og analysér", type="primary", icon=":material/play_arrow:"):
            submitted = RawClinicalData(
                patient_pseudonym=pseudonym,
                age=int(age) if age is not None else None,
                sex=sex.value if sex else "",
                weight_kg=weight,
                creatinine_umol_l=creatinine,
                egfr_reported=egfr,
                medications_text=medications,
                diagnoses_text=diagnoses,
                dispensings_text=dispensings,
                symptoms_text=symptoms,
            )
            state.set_raw_input(submitted)
            _import(submitted, is_demo=False)


def _as_float(value: float | None) -> float | None:
    # st.number_input kræver samme taltype for værdi og grænser.
    return float(value) if value is not None else None


def _import(raw: RawClinicalData, is_demo: bool) -> None:
    review = state.get_review()
    try:
        warnings = get_service().import_data(review, raw, is_demo=is_demo)
    except ClinicalEngineError as error:
        state.set_import_warnings([])
        st.error(f"Data er gemt, men analysen fejlede. {error}", icon=":material/error:")
        return
    except TelefarmError as error:
        st.error(str(error), icon=":material/error:")
        return

    state.set_import_warnings(warnings)
    state.flash(f"{len(review.medications)} lægemidler indsat og analyseret.")
    if warnings:
        st.rerun()
    go_to(PageKey.MEDICATIONS)
