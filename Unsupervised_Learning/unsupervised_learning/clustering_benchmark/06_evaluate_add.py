# -*- coding: utf-8 -*-
"""Evaluation for the ADDED dataset + cross-dataset comparison.

Part A: same metric suite as 03_evaluate.py, against the existing
        clusters_add/ labeling (baseline).
Part B: cross-dataset consistency — molecules present in BOTH datasets
        (matched by SMILES triple): do the two independent clustering runs
        (original clusters/ vs clusters_add/) assign them consistently?
        Computed for the existing pipeline and for each benchmark method.
Part C: best-cluster identity per labeling (which cluster wins on prob_SR /
        prob_YM) across both datasets.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_mutual_info_score, adjusted_rand_score,
                             calinski_harabasz_score, davies_bouldin_score,
                             normalized_mutual_info_score, silhouette_score)

from common import (K, SEED, SMILE_COLS, load_labels, load_source,
                    rebuild_existing_labels)

BASE_DIR = Path(__file__).resolve().parent
RESULTS = BASE_DIR / "results"
RESULTS_ADD = BASE_DIR / "results_add"
FIG_ADD = RESULTS_ADD / "figures"

N_BOOTSTRAP = 20
BOOT_FRAC = 0.8


def load_labels_add(name):
    return np.load(RESULTS_ADD / "labels" / f"{name}.npy")


def load_add():
    df = pd.read_csv(RESULTS_ADD / "source_add.csv", encoding="utf-8-sig")
    existing = np.load(RESULTS_ADD / "labels_existing_add.npy")
    return df, existing


def silhouette_own(name, labels, X_pca, XY):
    mask = labels != -1
    space = XY if ("umap2d" in name or name == "existing") else X_pca
    return silhouette_score(space[mask], labels[mask], metric="euclidean")


def cluster_statistics(df, labels, name):
    rows = []
    ym_log = df["Young's Modulus (kPa) log10"].to_numpy()
    for lbl in sorted(set(labels.tolist())):
        m = labels == lbl
        size = int(m.sum())
        if size == 0:
            continue
        sr = df.loc[m, "Swelling Ratio (times)"].ge(9).mean()
        ym = df.loc[m, "Young's Modulus (kPa)"].between(100, 2000).mean()
        rows.append((lbl, size, round(float(sr), 4), round(float(ym), 4)))
    out = pd.DataFrame(rows, columns=["cluster", "size", "prob_SR", "prob_YM"])
    out.to_csv(RESULTS_ADD / f"cluster_statistics_{name}_add.csv", index=False)

    groups = [ym_log[labels == c] for c in sorted(set(labels.tolist())) if c != -1]
    groups = [g[~np.isnan(g)] for g in groups]
    groups = [g for g in groups if len(g) >= 3]
    stat, p = kruskal(*groups)
    return out, float(p)


def bootstrap_ari(fit_fn, labels_full):
    n = len(labels_full)
    rng = np.random.default_rng(SEED)
    scores = []
    for _ in range(N_BOOTSTRAP):
        idx = np.sort(rng.choice(n, size=int(n * BOOT_FRAC), replace=False))
        scores.append(adjusted_rand_score(labels_full[idx], fit_fn(idx)))
    return float(np.mean(scores)), float(np.std(scores))


def key_map(df, labels):
    keys = df[SMILE_COLS].astype(str).agg("|".join, axis=1)
    return dict(zip(keys, labels))


def best_clusters(df, labels):
    ym_log = df["Young's Modulus (kPa) log10"].to_numpy()
    recs = []
    for lbl in sorted(set(labels.tolist())):
        if lbl == -1:
            continue
        m = labels == lbl
        recs.append((lbl, int(m.sum()),
                     float(df.loc[m, "Swelling Ratio (times)"].ge(9).mean()),
                     float(df.loc[m, "Young's Modulus (kPa)"].between(100, 2000).mean())))
    t = pd.DataFrame(recs, columns=["cluster", "size", "prob_SR", "prob_YM"])
    return int(t.loc[t.prob_SR.idxmax()].cluster), int(t.loc[t.prob_YM.idxmax()].cluster)


def main():
    # ---------- Part A: metric suite on added data ----------
    df_add, existing_add = load_add()
    X_add = np.load(RESULTS_ADD / "AB_concat1024_add.npy")
    X_pca = PCA(n_components=64, random_state=SEED).fit_transform(X_add)
    XY = np.load(RESULTS_ADD / "umap2d_add.npy")
    print(f"[OK] Added data: df={df_add.shape}")

    labelings = {
        "existing": existing_add,
        "pca64_kmeans": load_labels_add("pca64_kmeans"),
        "hdbscan_umap2d": load_labels_add("hdbscan_umap2d_mcs50"),
    }

    def fit_kmeans(idx):
        return KMeans(n_clusters=K, n_init=10,
                      random_state=SEED).fit_predict(X_pca[idx])

    def fit_hdb_umap(idx):
        return HDBSCAN(min_cluster_size=50,
                       metric="euclidean").fit_predict(XY[idx])

    fit_fns = {"pca64_kmeans": fit_kmeans, "hdbscan_umap2d": fit_hdb_umap}

    rows = []
    best_rows = []
    for name, labels in labelings.items():
        n_clusters = len([c for c in set(labels.tolist()) if c != -1])
        noise = float((labels == -1).mean())
        sil = silhouette_own(name, labels, X_pca, XY)
        Xe = XY if ("umap2d" in name or name == "existing") else X_pca
        mask = labels != -1
        db = davies_bouldin_score(Xe[mask], labels[mask])
        ch = calinski_harabasz_score(Xe[mask], labels[mask])
        ari = adjusted_rand_score(existing_add, labels)
        nmi = normalized_mutual_info_score(existing_add, labels)
        ami = adjusted_mutual_info_score(existing_add, labels)
        b_mean, b_std = (bootstrap_ari(fit_fns[name], labels)
                         if name in fit_fns else (float("nan"), float("nan")))
        stats_tbl, kw_p = cluster_statistics(df_add, labels, name)
        rows.append({"labeling": name, "n_clusters": n_clusters,
                     "noise_frac": round(noise, 4), "silhouette": round(sil, 4),
                     "davies_bouldin": round(db, 4),
                     "calinski_harabasz": round(ch, 1),
                     "ARI_vs_existing_add": round(ari, 4),
                     "NMI_vs_existing_add": round(nmi, 4),
                     "AMI_vs_existing_add": round(ami, 4),
                     "bootstrap_ARI_mean": round(b_mean, 4),
                     "bootstrap_ARI_std": round(b_std, 4),
                     "kruskal_YM_p": f"{kw_p:.2e}"})
        print(f"[OK] {name}: ARI={ari:.3f} sil={sil:.3f} bootARI={b_mean:.3f} "
              f"KW_p={kw_p:.1e}")
        print(stats_tbl.to_string(index=False))
        b_sr, b_ym = best_clusters(df_add, labels)
        best_rows.append(("add", name, b_sr, b_ym))

    table = pd.DataFrame(rows)
    table.to_csv(RESULTS_ADD / "comparison_table_add.csv", index=False)
    print(table.to_string(index=False))

    # ---------- Part B: cross-dataset consistency ----------
    df_orig, _ = load_source()
    existing_orig = rebuild_existing_labels(df_orig)

    orig_labelings = {
        "existing": existing_orig,
        "pca64_kmeans": load_labels("pca64_kmeans"),
        "hdbscan_umap2d": load_labels("hdbscan_umap2d_mcs50"),
    }

    cross_rows = []
    for method, labels_o in orig_labelings.items():
        map_o = key_map(df_orig, labels_o)
        map_a = key_map(df_add, labelings[method])
        shared = [k for k in map_o if k in map_a]
        lo = np.array([map_o[k] for k in shared])
        la = np.array([map_a[k] for k in shared])
        ari = adjusted_rand_score(lo, la)
        frac_same = float((lo == la).mean())
        cross_rows.append({"method": method, "n_shared": len(shared),
                           "ARI_orig_vs_add": round(ari, 4),
                           "frac_same_label": round(frac_same, 4)})
        print(f"[CROSS] {method}: n={len(shared)}, ARI={ari:.3f}, "
              f"same-label={frac_same:.1%}")
    pd.DataFrame(cross_rows).to_csv(RESULTS_ADD / "cross_dataset_summary.csv",
                                    index=False)

    # ---------- Part C: best cluster across datasets ----------
    for method, labels_o in orig_labelings.items():
        b_sr, b_ym = best_clusters(df_orig, labels_o)
        best_rows.append(("orig", method, b_sr, b_ym))
    pd.DataFrame(best_rows,
                 columns=["dataset", "labeling", "best_SR_cluster",
                          "best_YM_cluster"]).to_csv(
        RESULTS_ADD / "best_cluster_summary.csv", index=False)
    print("[OK] best_cluster_summary.csv saved")

    # ---------- figures ----------
    FIG_ADD.mkdir(parents=True, exist_ok=True)
    n = len(labelings)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows),
                             dpi=300)
    axes = np.atleast_1d(axes).ravel()
    for ax, (name, labels) in zip(axes, labelings.items()):
        noise = labels == -1
        ax.scatter(XY[noise, 0], XY[noise, 1], c="lightgray", s=4)
        ax.scatter(XY[~noise, 0], XY[~noise, 1], c=labels[~noise], s=4,
                   cmap="tab10")
        ari = adjusted_rand_score(existing_add, labels)
        ax.set_title(f"{name} (ARI={ari:.2f})", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in axes[n:]:
        ax.axis("off")
    fig.suptitle("Added dataset: clusterings on UMAP-2D (color = cluster)")
    fig.tight_layout()
    fig.savefig(FIG_ADD / "umap_scatter_add.png", bbox_inches="tight")
    plt.close(fig)

    names = [nm for nm in labelings if nm != "existing"]
    fig, axes = plt.subplots(1, len(names), figsize=(3.2 * len(names), 3.4),
                             dpi=300)
    for ax, name in zip(np.atleast_1d(axes).ravel(), names):
        ct = pd.crosstab(existing_add, labelings[name])
        ax.imshow(ct.values, cmap="Blues")
        ax.set_xticks(range(ct.shape[1]), ct.columns, fontsize=6)
        ax.set_yticks(range(ct.shape[0]), ct.index, fontsize=6)
        ax.set_xlabel(name, fontsize=8)
        ax.set_ylabel("existing_add", fontsize=8)
        for i in range(ct.shape[0]):
            for j in range(ct.shape[1]):
                if ct.values[i, j] > 0:
                    ax.text(j, i, ct.values[i, j], ha="center", va="center",
                            fontsize=6)
    fig.suptitle("Added dataset: contingency vs existing")
    fig.tight_layout()
    fig.savefig(FIG_ADD / "contingency_add.png", bbox_inches="tight")
    plt.close(fig)

    t = table.set_index("labeling")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=300)
    t["silhouette"].plot.bar(ax=axes[0], color="steelblue")
    axes[0].set_title("Added: silhouette (own space)")
    t["ARI_vs_existing_add"].plot.bar(ax=axes[1], color="darkorange")
    axes[1].set_title("Added: ARI vs existing")
    for ax in axes:
        ax.tick_params(axis="x", labelsize=8, rotation=30)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_ADD / "metric_bars_add.png", bbox_inches="tight")
    plt.close(fig)

    print("[OK] Figures -> results_add/figures/")


if __name__ == "__main__":
    main()
