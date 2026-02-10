# backend/app/etchfdc/pipeline/steps/raw_step.py
from __future__ import annotations
import json
from typing import Dict, Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def run_raw_step(ctx, *, inventory: Dict[str, Any]) -> Dict[str, Any]:
    sp = ctx.step_processed_dir("raw")
    figdir = ctx.step_figures_dir("raw")

    inv_path = sp / "inventory.json"
    inv_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    wafers = inventory.get("wafers", []) or []
    exp_counts: Dict[str, int] = {}
    for w in wafers:
        exp = str(w.get("exp_id") or "unknown")
        exp_counts[exp] = exp_counts.get(exp, 0) + 1

    plt.figure()
    plt.title("Wafer count by experiment")
    if exp_counts:
        plt.bar(list(exp_counts.keys()), list(exp_counts.values()))
    plt.tight_layout()
    out_png = figdir / "exp_counts.png"
    plt.savefig(out_png, dpi=150)
    plt.close()

    return {"row_count": len(wafers), "artifacts": ["exp_counts.png", "inventory.json"]}
