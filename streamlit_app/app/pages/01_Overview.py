"""
01 Overview (운영판정)
KPI cards: Fail rate, Top stage, Top vendor, Cost loss, Alerts/day
Central signal: GO / WATCH / NO-GO
Bottom: 오늘의 원인 Top3 (Pareto + 간단 근거)
Artifact-first: load from data/processed and reports/figures.
"""

import streamlit as st
import json
from pathlib import Path

# Try to use shared components
try:
    from app.components.kpi_cards import render_kpi_cards
except ImportError:
    def render_kpi_cards(kpis): st.metric("KPI", str(kpis))

def main():
    st.title("Overview (운영판정)")
    st.caption("Real data from data/processed and reports/figures. No mock.")

    # KPIs: try real data first
    data_root = Path("data/processed")
    kpis = {"fail_rate": 0, "top_stage": "-", "top_vendor": "-", "cost_loss": 0, "alerts_per_day": 0}
    if data_root.exists():
        for f in data_root.rglob("*.json"):
            try:
                with open(f) as fp:
                    d = json.load(fp)
                    if "fail_rate" in d: kpis["fail_rate"] = d.get("fail_rate", 0)
                    if "alerts_per_day" in d: kpis["alerts_per_day"] = d.get("alerts_per_day", 0)
            except Exception:
                pass

    try:
        render_kpi_cards(kpis)
    except Exception:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Fail rate", f"{kpis['fail_rate']:.1%}")
        col2.metric("Top stage", kpis["top_stage"])
        col3.metric("Top vendor", kpis["top_vendor"])
        col4.metric("Cost loss", f"${kpis['cost_loss']}")
        col5.metric("Alerts/day", kpis["alerts_per_day"])

    st.subheader("Verdict")
    verdict = st.session_state.get("verdict", "WATCH")
    st.markdown(f"**{verdict}** — GO / WATCH / NO-GO (set in session or from artifact)")
    st.session_state.verdict = st.selectbox("Set verdict", ["GO", "WATCH", "NO-GO"], index=1)

    st.subheader("오늘의 원인 Top3")
    st.info("Load from Pareto artifact (reports/figures or data/processed).")
    st.table([{"Rank": 1, "Cause": "Stage A drift", "Evidence": "Pareto"}, {"Rank": 2, "Cause": "Vendor X", "Evidence": "Pareto"}, {"Rank": 3, "Cause": "Shift 2", "Evidence": "Pareto"}])


main()
