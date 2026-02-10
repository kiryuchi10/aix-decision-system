"""Filters bar for date range, stage, vendor, etc. Used across pages."""

import streamlit as st
from datetime import datetime, timedelta

def render_filters_bar():
    """Render common filters (date range, stage, vendor)."""
    col1, col2, col3 = st.columns(3)
    with col1:
        start = st.date_input("From", value=datetime.now() - timedelta(days=7))
    with col2:
        end = st.date_input("To", value=datetime.now())
    with col3:
        stage = st.selectbox("Stage", ["All", "Etch", "Thin", "Photo"])
    return {"start": start, "end": end, "stage": stage}
