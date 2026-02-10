"""
RCA Defect Prediction — Streamlit entry (multipage).
Run from streamlit_app/: streamlit run app/dashboard.py
Streamlit auto-discovers app/pages/ (01_Overview.py, 02_..., etc.).
No mock; use real CSV/model artifacts from data/ and models/.
"""

import streamlit as st

st.set_page_config(
    page_title="RCA Defect Prediction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Shared state
if "selected_dataset_id" not in st.session_state:
    st.session_state.selected_dataset_id = None
if "last_run_step" not in st.session_state:
    st.session_state.last_run_step = None
if "verdict" not in st.session_state:
    st.session_state.verdict = "WATCH"

st.sidebar.title("RCA Defect Prediction")
st.sidebar.caption("Artifact-first, no mock. Use DataHub then run steps.")
st.sidebar.markdown("---")
st.sidebar.markdown("**Pages** (in sidebar below) come from `app/pages/`.")
st.title("Home")
st.info("Select a page from the sidebar: 01 Overview, 02 RCA Explorer, 03 Predictions, 04 Cost Impact, 05 Viz Automation.")
