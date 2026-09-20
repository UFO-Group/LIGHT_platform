# -*- coding: utf-8 -*-
"""Shared utilities for the clustering benchmark.

Scope: ORIGINAL dataset only (1291 samples, final_two_smiles_with_modulus.csv).
The `_add` extended dataset is intentionally NOT used here.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

SEED = 42
K = 6
PCA_N_COMPONENTS = 64

BASE_DIR = Path(__file__).resolve().parent
UL_DIR = BASE_DIR.parent                    # unsupervised_learning/
RESULTS_DIR = BASE_DIR / "results"
FIG_DIR = RESULTS_DIR / "figures"
LABELS_DIR = RESULTS_DIR / "labels"

NPY_PATH = UL_DIR / "AB_concat1024.npy"
UMAP_PATH = UL_DIR / "umap2d.npy"
CSV_PATH = UL_DIR / "final_two_smiles_with_modulus.csv"
CLUSTERS_DIR = UL_DIR / "clusters"

SMILE_COLS = ["SMILE A", "SMILE B", "SMILE C"]


def load_source():
    """Return (df, X): source dataframe and pooled Morgan count fingerprints."""
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    X = np.load(NPY_PATH)
    if len(df) != len(X):
        raise ValueError(f"CSV rows ({len(df)}) != NPY samples ({len(X)})")
    return df, X


def rebuild_existing_labels(df):
    """Reconstruct the label vector implicit in clusters/cluster_{0..5}.csv.

    The cluster CSVs are row subsets of the source dataframe (boolean-mask
    order preserved), so a first-unmatched exact-match scan on the SMILES
    triple reconstructs labels. A `used` guard prevents duplicate rows from
    being claimed twice. Some cluster CSVs were re-uploaded with a Chinese
    `来源` column, so only SMILES columns are used as keys.
    """
    labels = np.full(len(df), -1, dtype=int)
    used = np.zeros(len(df), dtype=bool)
    src_keys = df[SMILE_COLS].astype(str).agg("|".join, axis=1).tolist()

    per_cluster_counts = {}
    for lbl in range(K):
        cdf = pd.read_csv(CLUSTERS_DIR / f"cluster_{lbl}.csv", encoding="utf-8-sig")
        keys = cdf[SMILE_COLS].astype(str).agg("|".join, axis=1).tolist()
        per_cluster_counts[lbl] = len(keys)
        for key in keys:
            idx = next(
                (i for i in range(len(src_keys)) if not used[i] and src_keys[i] == key),
                None,
            )
            if idx is None:
                raise ValueError(
                    f"cluster_{lbl}.csv key not found (or already used): {key}"
                )
            used[idx] = True
            labels[idx] = lbl

    if not used.all():
        raise ValueError(f"{int((~used).sum())} source rows not assigned to any cluster")

    print("[OK] Reconstructed existing labels from clusters/cluster_0..5.csv")
    for lbl, cnt in per_cluster_counts.items():
        print(f"     cluster {lbl}: {cnt} rows")
    return labels


def get_pca64(X):
    """PCA-64 projection, same parameters as unsupervised.py."""
    pca = PCA(n_components=PCA_N_COMPONENTS, random_state=SEED)
    return pca.fit_transform(X)


def save_labels(name, labels):
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    np.save(LABELS_DIR / f"{name}.npy", np.asarray(labels))
    print(f"[OK] Saved labels -> results/labels/{name}.npy")


def load_labels(name):
    return np.load(LABELS_DIR / f"{name}.npy")


def save_cluster_csvs(name, labels, df):
    """Mirror the clusters/cluster_{i}.csv convention into results/clusters_<name>/."""
    out_dir = RESULTS_DIR / f"clusters_{name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for lbl in sorted(set(np.asarray(labels).tolist())):
        if lbl == -1:
            continue
        df_sub = df[np.asarray(labels) == lbl]
        df_sub.to_csv(out_dir / f"cluster_{lbl}.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] Saved cluster splits -> results/clusters_{name}/")
