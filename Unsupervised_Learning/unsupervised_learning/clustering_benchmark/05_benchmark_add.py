# -*- coding: utf-8 -*-
"""Run the 2-method clustering benchmark on the ADDED dataset (n=1303).

Mirrors 01/02 on the original data:
  Method 1: k-means in PCA-64 (+ silhouette-k sweep)
  Method 2: HDBSCAN on UMAP-2D, mcs sweep
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from umap import UMAP

from common import SEED

BASE_DIR = Path(__file__).resolve().parent
RESULTS_ADD = BASE_DIR / "results_add"
LABELS_ADD = RESULTS_ADD / "labels"
FIG_ADD = RESULTS_ADD / "figures"
UMAP2D_ADD = RESULTS_ADD / "umap2d_add.npy"

K = 6
PCA_N = 64
MIN_CLUSTER_SIZES = (25, 50, 100)
MAIN_MCS = 50


def save_labels(name, labels):
    LABELS_ADD.mkdir(parents=True, exist_ok=True)
    np.save(LABELS_ADD / f"{name}.npy", np.asarray(labels))
    print(f"[OK] Saved labels -> results_add/labels/{name}.npy")


def save_cluster_csvs(name, labels, df):
    out_dir = RESULTS_ADD / f"clusters_{name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for lbl in sorted(set(np.asarray(labels).tolist())):
        if lbl == -1:
            continue
        df[np.asarray(labels) == lbl].to_csv(
            out_dir / f"cluster_{lbl}.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] Saved cluster splits -> results_add/clusters_{name}/")


def k_sweep_csv(rows, path, title, png):
    np.savetxt(path, np.array(rows), delimiter=",",
               header="k,silhouette", comments="", fmt=["%d", "%.6f"])
    ks, ss = zip(*rows)
    plt.figure(figsize=(6, 4), dpi=300)
    plt.plot(ks, ss, "o-")
    plt.axvline(K, color="gray", linestyle="--", label=f"K={K} (pipeline)")
    plt.xlabel("k")
    plt.ylabel("Silhouette")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(png)
    plt.close()


def main():
    df = pd.read_csv(RESULTS_ADD / "source_add.csv", encoding="utf-8-sig")
    X = np.load(RESULTS_ADD / "AB_concat1024_add.npy")
    assert len(df) == len(X)
    print(f"[OK] Added dataset: df={df.shape}, X={X.shape}")

    pca = PCA(n_components=PCA_N, random_state=SEED)
    X_pca = pca.fit_transform(X)
    print(f"[OK] PCA-64: {X_pca.shape}")

    # ---------- Method 1: k-means on PCA-64 ----------
    labels_km = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit_predict(X_pca)
    print(f"[OK] pca64_kmeans counts: {dict(zip(*np.unique(labels_km, return_counts=True)))}")
    save_labels("pca64_kmeans", labels_km)
    save_cluster_csvs("pca64_kmeans", labels_km, df)
    rows = []
    for k in range(4, 11):
        lab = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(X_pca)
        s = silhouette_score(X_pca, lab, metric="euclidean")
        rows.append((k, s))
        print(f"[INFO] k={k}: silhouette={s:.4f}")
    FIG_ADD.mkdir(parents=True, exist_ok=True)
    k_sweep_csv(rows, RESULTS_ADD / "silhouette_k_pca64_add.csv",
                "k-means (PCA-64, added): silhouette vs k",
                FIG_ADD / "silhouette_k_pca64_add.png")

    # ---------- Method 2: HDBSCAN on UMAP-2D ----------
    if UMAP2D_ADD.exists():
        XY = np.load(UMAP2D_ADD)
    else:
        print("[INFO] Computing UMAP-2D for added data (single-core)...")
        um = UMAP(n_components=2, n_neighbors=30, min_dist=0.1,
                  metric="euclidean", random_state=SEED, n_jobs=1)
        XY = um.fit_transform(X_pca)
        np.save(UMAP2D_ADD, XY)

    summary = []
    for mcs in MIN_CLUSTER_SIZES:
        labels = HDBSCAN(min_cluster_size=mcs, metric="euclidean",
                         cluster_selection_method="eom").fit_predict(XY)
        name = f"hdbscan_umap2d_mcs{mcs}"
        noise = int((labels == -1).sum())
        n_clusters = len([c for c in set(labels.tolist()) if c != -1])
        print(f"[OK] {name}: clusters={n_clusters}, noise={noise} "
              f"({noise / len(labels):.1%}), "
              f"sizes={dict(zip(*np.unique(labels, return_counts=True)))}")
        summary.append((name, "umap2d", mcs, n_clusters, noise))
        save_labels(name, labels)

    main_labels = HDBSCAN(min_cluster_size=MAIN_MCS, metric="euclidean",
                          cluster_selection_method="eom").fit_predict(XY)
    save_labels("hdbscan_main", main_labels)
    save_cluster_csvs("hdbscan_main", main_labels, df)

    with open(RESULTS_ADD / "hdbscan_sweep_add.csv", "w", encoding="utf-8") as f:
        f.write("name,space,min_cluster_size,n_clusters,noise\n")
        for row in summary:
            f.write(",".join(str(x) for x in row) + "\n")
    print(f"[INFO] Main config: HDBSCAN@UMAP2D, min_cluster_size={MAIN_MCS}")


if __name__ == "__main__":
    main()
