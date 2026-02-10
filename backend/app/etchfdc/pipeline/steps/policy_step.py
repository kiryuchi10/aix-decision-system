# backend/app/etchfdc/pipeline/steps/policy_step.py
from __future__ import annotations
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def run_policy_step(ctx, scores: np.ndarray) -> dict:
    sp = ctx.step_processed_dir("policy")
    figdir = ctx.step_figures_dir("policy")

    scores = np.asarray(scores, dtype=float).ravel()
    if scores.size == 0:
        (sp / "policy.json").write_text(json.dumps({"threshold": 0, "rule": "no data"}, indent=2), encoding="utf-8")
        return {"artifacts": ["policy.json"]}

    thresholds = np.linspace(float(scores.min()), float(scores.max()), 50)
    alarm_rate = [(scores >= t).mean() for t in thresholds]

    plt.figure(figsize=(6, 4))
    plt.title("Alarm volume vs threshold")
    plt.plot(thresholds, alarm_rate)
    plt.tight_layout()
    plt.savefig(figdir / "alarm_volume.png", dpi=150)
    plt.close()

    target = 0.05
    idx = int(np.argmin([abs(a - target) for a in alarm_rate]))
    chosen = float(thresholds[idx])
    policy = {"threshold": chosen, "rule": "RED if score>=threshold else GREEN", "target_alarm_rate": target}
    (sp / "policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    return {"artifacts": ["alarm_volume.png", "policy.json"]}
