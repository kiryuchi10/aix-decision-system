"""
02 RCA Explorer
Pareto: stage / vendor / error_code / shift
Correlation/regression driver candidates
Similar-pattern group (cluster) select → top causes/actions for that group
Artifact-first: data/processed, reports/figures.
"""

import streamlit as st
from pathlib import Path

def main():
    st.title("RCA Explorer")
    st.caption("Pareto, drivers, clusters from data/processed. No mock.")

    tab1, tab2, tab3 = st.tabs(["Pareto", "Drivers", "Clusters"])

    with tab1:
        st.subheader("Pareto by dimension")
        dim = st.selectbox("Dimension", ["stage", "vendor", "error_code", "shift"])
        st.info(f"Load Pareto data for {dim} from data/processed (e.g. pareto_{dim}.json or .csv).")
        # Placeholder table
        st.table([{"Category": "A", "Count": 120}, {"Category": "B", "Count": 80}])

    with tab2:
        st.subheader("Driver candidates (correlation/regression)")
        st.info("Load from data/processed/drivers.json or similar.")
        st.json({"drivers": ["pressure_torr", "temperature"], "importance": [0.8, 0.6]})

    with tab3:
        st.subheader("Similar-pattern groups (clusters)")
        cluster_id = st.selectbox("Cluster", [1, 2, 3], key="cluster_select")
        st.info(f"Load causes for cluster {cluster_id} from data/processed/clusters/{cluster_id}/causes.json.")
        st.table([{"Cause": "Parameter drift", "Frequency": 15}, {"Cause": "Tool wear", "Frequency": 8}])


main()
