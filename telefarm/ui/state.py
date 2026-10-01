"""Det ENESTE sted der læser og skriver st.session_state for gennemgangen.

Alt lever kun i brugerens session – intet gemmes permanent.
"""

from __future__ import annotations

import streamlit as st

from telefarm.application.dto import RawClinicalData
from telefarm.domain.models import Review

_REVIEW_KEY = "telefarm.review"
_RAW_INPUT_KEY = "telefarm.raw_input"
_FORM_VERSION_KEY = "telefarm.form_version"
_IMPORT_WARNINGS_KEY = "telefarm.import_warnings"
_FLASH_KEY = "telefarm.flash"


def get_review() -> Review:
    if _REVIEW_KEY not in st.session_state:
        st.session_state[_REVIEW_KEY] = Review()
    return st.session_state[_REVIEW_KEY]


def reset_review() -> None:
    st.session_state[_REVIEW_KEY] = Review()
    st.session_state[_RAW_INPUT_KEY] = RawClinicalData()
    st.session_state[_IMPORT_WARNINGS_KEY] = []
    _bump_form_version()


def get_raw_input() -> RawClinicalData:
    return st.session_state.get(_RAW_INPUT_KEY, RawClinicalData())


def set_raw_input(raw: RawClinicalData, refresh_form: bool = False) -> None:
    """Husker det indsatte input. `refresh_form` genindlæser formularfelterne (fx ved demo)."""
    st.session_state[_RAW_INPUT_KEY] = raw
    if refresh_form:
        _bump_form_version()


def form_version() -> int:
    return st.session_state.get(_FORM_VERSION_KEY, 0)


def _bump_form_version() -> None:
    # Nye widget-nøgler får Streamlit til at bruge de nye standardværdier.
    st.session_state[_FORM_VERSION_KEY] = form_version() + 1


def get_import_warnings() -> list[str]:
    return st.session_state.get(_IMPORT_WARNINGS_KEY, [])


def set_import_warnings(warnings: list[str]) -> None:
    st.session_state[_IMPORT_WARNINGS_KEY] = list(warnings)


def flash(message: str, icon: str = ":material/check_circle:") -> None:
    """Besked der vises som toast efter næste sideskift/genkørsel."""
    st.session_state.setdefault(_FLASH_KEY, []).append((message, icon))


def pop_flashes() -> list[tuple[str, str]]:
    return st.session_state.pop(_FLASH_KEY, [])
