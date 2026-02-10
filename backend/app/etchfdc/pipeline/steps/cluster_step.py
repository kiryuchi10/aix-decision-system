# backend/app/etchfdc/pipeline/steps/cluster_step.py
from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def run_cluster_step(ctx, X_features: pd.DataFrame) -> dict:
    sp = ctx.step_processed_dir("cluster")
    figdir = ctx.step_figures_dir("cluster")

    k = 3 if X_features.shape[0] >= 3 else 1
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = km.fit_predict(X_features)

    if k > 1:
        s = silhouette_score(X_features, labels)
        plt.figure(figsize=(5, 3))
        plt.title(f"Silhouette score (k={k}) = {s:.3f}")
        plt.bar(["silhouette"], [s])
        plt.tight_layout()
        plt.savefig(figdir / "silhouette.png", dpi=150)
        plt.close()

    df = pd.DataFrame({"cluster": labels})
    df.to_csv(sp / "clusters.csv", index=False)
    return {"artifacts": ["silhouette.png", "clusters.csv"] if k > 1 else ["clusters.csv"]}
