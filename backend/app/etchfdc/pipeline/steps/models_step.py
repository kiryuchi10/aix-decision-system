# backend/app/etchfdc/pipeline/steps/models_step.py
from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve, auc, precision_recall_curve


def run_models_step(ctx, X_features: pd.DataFrame, y) -> dict:
    sp = ctx.step_processed_dir("models")
    figdir = ctx.step_figures_dir("models")

    if y is None:
        (sp / "note.json").write_text('{"status":"no_label"}', encoding="utf-8")
        return {"artifacts": ["note.json"]}

    stratify = y if len(set(y)) > 1 else None
    Xtr, Xte, ytr, yte = train_test_split(X_features, y, test_size=0.3, random_state=42, stratify=stratify)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(Xtr, ytr)
    prob = clf.predict_proba(Xte)[:, 1]

    fpr, tpr, _ = roc_curve(yte, prob)
    roc_auc = auc(fpr, tpr)
    plt.figure()
    plt.title(f"ROC AUC={roc_auc:.3f}")
    plt.plot(fpr, tpr)
    plt.plot([0, 1], [0, 1], "--")
    plt.tight_layout()
    plt.savefig(figdir / "roc.png", dpi=150)
    plt.close()

    p, r, _ = precision_recall_curve(yte, prob)
    plt.figure()
    plt.title("Precision-Recall")
    plt.plot(r, p)
    plt.tight_layout()
    plt.savefig(figdir / "pr.png", dpi=150)
    plt.close()

    return {"artifacts": ["roc.png", "pr.png"]}
