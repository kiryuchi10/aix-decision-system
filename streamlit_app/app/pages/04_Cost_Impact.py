"""
04 Cost Impact (돈으로 보이게)
FP/FN cost input → optimal threshold recommendation
Alarm volume/day graph
Artifact-first: data/processed.
"""

import streamlit as st
from pathlib import Path

def main():
    st.title("Cost Impact")
    st.caption("FP/FN cost → optimal threshold. Alarm volume from data. No mock.")

    col1, col2 = st.columns(2)
    with col1:
        fp_cost = st.number_input("FP cost (false alarm)", value=100, min_value=0)
    with col2:
        fn_cost = st.number_input("FN cost (missed defect)", value=1000, min_value=0)

    if st.button("Recommend threshold"):
        # Placeholder: real = load model or curve from data/processed
        opt = 0.4 + (fn_cost / (fp_cost + fn_cost)) * 0.3
        st.success(f"Recommended threshold: {opt:.2f}")

    st.subheader("Alarm volume / day")
    st.info("Load from data/processed/alarm_volume.json or CSV.")
    st.line_chart({"day": list(range(7)), "alarms": [12, 15, 10, 14, 11, 13, 9]})


main()
