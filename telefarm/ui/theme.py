"""Indlæser applikationens CSS (farver og layout ud over Streamlit-temaet)."""

from functools import cache
from pathlib import Path

import streamlit as st

_STYLESHEET = Path(__file__).parent / "assets" / "styles.css"


@cache
def _stylesheet() -> str:
    return _STYLESHEET.read_text(encoding="utf-8")


def apply() -> None:
    st.html(f"<style>{_stylesheet()}</style>")
