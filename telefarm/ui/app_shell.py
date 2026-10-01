"""Applikationens ramme: tema, header, navigation, beskeder og sidefod."""

from __future__ import annotations

import streamlit as st

from telefarm.ui import navigation, state, theme
from telefarm.ui.components import header
from telefarm.ui.components.layout import footer
from telefarm.ui.routing import PageKey, go_to


def run() -> None:
    theme.apply()
    review = state.get_review()
    page = navigation.build(review)

    header.render(review, on_new_review=_new_review, on_open_report=lambda: go_to(PageKey.REPORT))
    for message, icon in state.pop_flashes():
        st.toast(message, icon=icon)

    page.run()
    footer(state.get_review())
    _sidebar_footer()


def _new_review() -> None:
    if state.get_review().has_data:
        _confirm_new_review()
    else:
        state.reset_review()
        go_to(PageKey.INSERT)


@st.dialog("Start ny gennemgang?")
def _confirm_new_review() -> None:
    st.write("Den aktuelle gennemgang, valgte fund og beslutninger slettes. "
             "Download rapporten først, hvis den skal gemmes.")
    cancel_col, confirm_col = st.columns(2)
    if cancel_col.button("Annullér", width="stretch"):
        st.rerun()
    if confirm_col.button("Start ny", type="primary", width="stretch"):
        state.reset_review()
        go_to(PageKey.INSERT)


def _sidebar_footer() -> None:
    with st.sidebar:
        st.html('<div class="tf-sidebar-spacer"></div>')
        st.caption(":material/verified_user: Kun denne session  \nIngen permanent lagring")
