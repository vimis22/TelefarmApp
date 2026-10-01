"""Fælles sidelayout: trinindikator, overskrift, fejlvisning og sidefod."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from telefarm.application.errors import TelefarmError
from telefarm.domain.models import Review
from telefarm.ui import state
from telefarm.ui.components import stepper
from telefarm.ui.routing import WorkflowStep


def page_frame(step: WorkflowStep, title: str, caption: str | None = None) -> None:
    stepper.render(step, state.get_review())
    st.html('<hr class="tf-rule tf-rule--spaced">')
    st.title(title)
    if caption:
        st.caption(caption)


def run_safely(action: Callable[[], object]) -> bool:
    """Kører en handling og viser forventede fejl som besked i stedet for et stacktrace."""
    try:
        action()
    except TelefarmError as error:
        st.error(str(error), icon=":material/error:")
        return False
    return True


def footer(review: Review) -> None:
    st.html('<hr class="tf-rule tf-rule--spaced">')
    if review.is_demo:
        st.caption("Fiktiv patient · kliniske fund, scores og kildedata er illustrative.")
    else:
        st.caption("Beslutningsstøtte · regler og kildedata er illustrative og skal verificeres klinisk.")
