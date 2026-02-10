# backend/app/etchfdc/pipeline/steps/pca_step.py
from __future__ import annotations
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


def run_pca_step(ctx, X_features: pd.DataFrame) -> dict:
    sp = ctx.step_processed_dir("pca")
    figdir = ctx.step_figures_dir("pca")

    n_comp = min(10, X_features.shape[1])
    if n_comp < 1:
        return {"artifacts": []}
    pca = PCA(n_components=n_comp)
    Z = pca.fit_transform(X_features)

    plt.figure(figsize=(6, 4))
    plt.title("PCA explained variance")
    plt.plot(pca.explained_variance_ratio_, marker="o")
    plt.tight_layout()
    plt.savefig(figdir / "scree.png", dpi=150)
    plt.close()

    if Z.shape[1] >= 2:
        plt.figure(figsize=(6, 5))
        plt.title("PCA scores (PC1 vs PC2)")
        plt.scatter(Z[:, 0], Z[:, 1], s=10)
        plt.tight_layout()
        plt.savefig(figdir / "scores.png", dpi=150)
        plt.close()

    pd.DataFrame(Z, columns=[f"PC{i+1}" for i in range(Z.shape[1])]).to_csv(sp / "pca_scores.csv", index=False)
    arts = ["scree.png", "scores.png", "pca_scores.csv"] if Z.shape[1] >= 2 else ["scree.png", "pca_scores.csv"]
    return {"artifacts": arts}
