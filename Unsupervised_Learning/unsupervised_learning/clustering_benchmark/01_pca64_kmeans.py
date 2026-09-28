# -*- coding: utf-8 -*-
"""Method 1: k-means in PCA-64 space (original data, k=6).

Also produces a silhouette-vs-k curve (k = 4..10) to sanity-check the
hard-coded K=6 of the existing pipeline.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from common import (FIG_DIR, RESULTS_DIR, K, SEED, get_pca64, load_source,
                    save_cluster_csvs, save_labels)


def main():
    df, X = load_source()
    X_pca = get_pca64(X)
    print(f"[OK] PCA-64 projection: {X_pca.shape}")

    km = KMeans(n_clusters=K, n_init=10, random_state=SEED)
    labels = km.fit_predict(X_pca)

    counts = dict(zip(*np.unique(labels, return_counts=True)))
    print("[OK] PCA-64 k-means cluster counts:", counts)

    sil = silhouette_score(X_pca, labels, metric="euclidean")
    print(f"[OK] Silhouette (euclidean, PCA-64): {sil:.4f}")

    save_labels("pca64_kmeans", labels)
    save_cluster_csvs("pca64_kmeans", labels, df)

    # ---- silhouette vs k ----
    rows = []
    for k in range(4, 11):
        lab = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(X_pca)
        s = silhouette_score(X_pca, lab, metric="euclidean")
        rows.append((k, s))
        print(f"[INFO] k={k}: silhouette={s:.4f}")

    np.savetxt(RESULTS_DIR / "silhouette_k_pca64.csv",
               np.array(rows), delimiter=",", header="k,silhouette", comments="",
               fmt=["%d", "%.6f"])

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ks, ss = zip(*rows)
    plt.figure(figsize=(6, 4), dpi=300)
    plt.plot(ks, ss, "o-")
    plt.axvline(K, color="gray", linestyle="--", label=f"K={K} (pipeline)")
    plt.xlabel("k")
    plt.ylabel("Silhouette (PCA-64, euclidean)")
    plt.title("k-means: silhouette vs k")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "silhouette_k_pca64.png")
    plt.close()
    print("[OK] Figure -> results/figures/silhouette_k_pca64.png")


if __name__ == "__main__":
    main()
