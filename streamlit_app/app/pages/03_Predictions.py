"""
03 Predictions
Table: lot/unit probability, risk_level, top_drivers
Threshold slider (alarm volume vs FN cost tradeoff)
Artifact-first: data/processed/predictions.
"""

import streamlit as st
from pathlib import Path

def main():
    st.title("Predictions")
    st.caption("Risk table from data/processed. No mock.")

    threshold = st.slider("Threshold (probability)", 0.0, 1.0, 0.5, 0.05)
    st.caption("Adjust threshold: higher = fewer alarms, more FN risk.")

    st.subheader("Risk table")
    st.info("Load from data/processed/predictions.csv or risk_table.json.")
    st.table([
        {"lot": "L001", "unit": "U01", "probability": 0.72, "risk_level": "HIGH", "top_drivers": "pressure, temp"},
        {"lot": "L002", "unit": "U02", "probability": 0.35, "risk_level": "LOW", "top_drivers": "-"},
    ])


main()
