"""KPI cards for Overview. Real data from data/processed."""

import streamlit as st
from pathlib import Path
import json

def render_kpi_cards(kpis: dict):
    """Render 5 KPI metrics. kpis: fail_rate, top_stage, top_vendor, cost_loss, alerts_per_day."""
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Fail rate", f"{kpis.get('fail_rate', 0):.1%}")
    col2.metric("Top stage", kpis.get("top_stage", "-"))
    col3.metric("Top vendor", kpis.get("top_vendor", "-"))
    col4.metric("Cost loss", f"${kpis.get('cost_loss', 0):,.0f}")
    col5.metric("Alerts/day", kpis.get("alerts_per_day", 0))
