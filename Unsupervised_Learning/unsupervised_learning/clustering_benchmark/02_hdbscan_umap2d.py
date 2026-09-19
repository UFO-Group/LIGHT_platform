# -*- coding: utf-8 -*-
"""Method 2: HDBSCAN on the existing UMAP-2D coordinates (original data).

The literal "UMAP then HDBSCAN" option. min_cluster_size is swept over
{25, 50, 100}; noise points get label -1. sklearn>=1.3 ships HDBSCAN,
so no new dependency is required.
"""
import numpy as np
from sklearn.cluster import HDBSCAN

from common import (RESULTS_DIR, UMAP_PATH, load_source, save_cluster_csvs,
                    save_labels)

MIN_CLUSTER_SIZES = (25, 50, 100)
MAIN_MCS = 50  # primary configuration carried into 03_evaluate.py


def run_hdbscan(XY, mcs):
    return HDBSCAN(min_cluster_size=mcs, metric="euclidean",
                   cluster_selection_method="eom").fit_predict(XY)


def describe(name, labels):
    counts = dict(zip(*np.unique(labels, return_counts=True)))
    noise = int((labels == -1).sum())
    n_clusters = len([c for c in counts if c != -1])
    print(f"[OK] {name}: clusters={n_clusters}, noise={noise} "
          f"({noise / len(labels):.1%}), sizes={counts}")
    return n_clusters, noise


def main():
    df, _ = load_source()
    XY = np.load(UMAP_PATH)
    print(f"[OK] UMAP-2D: {XY.shape}")

    summary = []
    for mcs in MIN_CLUSTER_SIZES:
        labels = run_hdbscan(XY, mcs)
        name = f"hdbscan_umap2d_mcs{mcs}"
        n_clusters, noise = describe(name, labels)
        summary.append((name, "umap2d", mcs, n_clusters, noise))
        save_labels(name, labels)

    # persist main configuration
    main_labels = run_hdbscan(XY, MAIN_MCS)
    save_labels("hdbscan_main", main_labels)
    save_cluster_csvs("hdbscan_main", main_labels, df)

    out = RESULTS_DIR / "hdbscan_sweep.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("name,space,min_cluster_size,n_clusters,noise\n")
        for row in summary:
            f.write(",".join(str(x) for x in row) + "\n")
    print(f"[OK] Sweep summary -> {out.name}")
    print(f"[INFO] Main configuration: HDBSCAN@UMAP2D, min_cluster_size={MAIN_MCS}")


if __name__ == "__main__":
    main()
