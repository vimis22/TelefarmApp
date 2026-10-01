"""Giver brugerfladen adgang til use cases uden at kende de konkrete adaptere."""

import streamlit as st

from telefarm.application.review_service import ReviewService
from telefarm.bootstrap import build_review_service


@st.cache_resource
def get_service() -> ReviewService:
    # Servicen er tilstandsløs; data ligger i hver brugers session (ui/state.py).
    return build_review_service()
