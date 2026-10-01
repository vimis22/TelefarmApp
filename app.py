"""Indgang til Streamlit-appen. Start med:  streamlit run app.py"""

import streamlit as st

from telefarm.ui import app_shell

st.set_page_config(
    page_title="Telefarmakologisk Ambulatorium",
    page_icon=":material/medication:",
    layout="wide",
)
app_shell.run()
