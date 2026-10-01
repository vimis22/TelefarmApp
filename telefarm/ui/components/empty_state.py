"""Tom tilstand med forklaring og én handling."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def empty_state(title: str, text: str, action_label: str | None = None,
                on_action: Callable[[], None] | None = None,
                icon: str = ":material/inbox:") -> None:
    with st.container(border=True):
        st.markdown(f"### {icon}\n#### {title}")
        st.markdown(text)
        if action_label and on_action and st.button(action_label, type="primary",
                                                    key=f"empty_state.{title}"):
            on_action()
