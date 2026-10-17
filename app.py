"""Streamlit entry point for the voice authenticity demo."""

import streamlit as st

from frontend.ui import render_app


st.set_page_config(
    page_title="Voice Authenticity Check",
    page_icon="🎙️",
    layout="wide",
)

render_app()
