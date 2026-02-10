"""Table helpers: load CSV/JSON from data/processed and display."""

import streamlit as st
from pathlib import Path
import json
import pandas as pd

def load_table(path: Path, max_rows: int = 100):
    """Load CSV or JSON from path; return DataFrame or None."""
    if not path.exists():
        return None
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, nrows=max_rows)
    if path.suffix.lower() == ".json":
        with open(path) as f:
            d = json.load(f)
        if isinstance(d, list):
            return pd.DataFrame(d)
        if "rows" in d:
            return pd.DataFrame(d["rows"])
        return pd.DataFrame([d])
    return None

def render_table(path: Path, max_rows: int = 100):
    """Load and display table from path."""
    df = load_table(path, max_rows)
    if df is not None:
        st.dataframe(df)
    else:
        st.info(f"No data at {path}")
