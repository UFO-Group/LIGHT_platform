# -*- coding: utf-8 -*-
"""Evaluation suite for the clustering benchmark (original data, n=1291).

For every labeling (existing pipeline + the two benchmark methods):
  - internal metrics: silhouette (in each method's OWN clustering space),
    Davies-Bouldin / Calinski-Harabasz
  - agreement with the existing pipeline: ARI / NMI / AMI + contingency
  - stability: bootstrap ARI (20 x 80% resampling, refit + compare on shared
    points); k-means seed sensitivity; UMAP seed sensitivity (3 seeds)
  - scientific validity: per-cluster prob_SR / prob_YM (same definitions as
    analyze_unsupervised.py) + Kruskal-Wallis across clusters (YM log10)

Outputs: results/comparison_table.csv, cluster_statistics_<method>.csv,
seed_stability.csv, figures under results/figures/.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.cluster import HDBSCAN, KMeans
from sklearn.metrics import (adjusted_mutual_info_score, adjusted_rand_score,
                             calinski_harabasz_score, davies_bouldin_score,
                             normalized_mutual_info_score, silhouette_score)
from umap import UMAP

from common import (FIG_DIR, K, RESULTS_DIR, SEED, UMAP_PATH, get_pca64,
                    load_labels, load_source, rebuild_existing_labels)

N_BOOTSTRAP = 20
BOOT_FRAC = 0.8


def silhouette_in_own_space(name, labels, X_pca, XY):
    mask = labels != -1
    space = XY if ("umap2d" in name or name == "existing") else X_pca
    return silhouette_score(space[mask], labels[mask], metric="euclidean")


def euclidean_space(name, X_pca, XY):
    if "umap2d" in name or name == "existing":
        return XY
    return X_pca


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
    out.to_csv(RESULTS_DIR / f"cluster_statistics_{name}.csv", index=False)

    groups = [ym_log[labels == c] for c in sorted(set(labels.tolist())) if c != -1]
    groups = [g[~np.isnan(g)] for g in groups]
    groups = [g for g in groups if len(g) >= 3]
    stat, p = kruskal(*groups)
    return out, float(stat), float(p)


def bootstrap_ari(fit_fn, labels_full):
    """Resample 80% of points, refit, ARI on the shared subset."""
    n = len(labels_full)
    rng = np.random.default_rng(SEED)
    scores = []
    for _ in range(N_BOOTSTRAP):
        idx = np.sort(rng.choice(n, size=int(n * BOOT_FRAC), replace=False))
        sub = fit_fn(idx)
        scores.append(adjusted_rand_score(labels_full[idx], sub))
    return float(np.mean(scores)), float(np.std(scores))


def main():
    df, X = load_source()
    X_pca = get_pca64(X)
    XY = np.load(UMAP_PATH)
    print("[OK] Data loaded")

    existing = rebuild_existing_labels(df)
    labelings = {
        "existing": existing,
        "pca64_kmeans": load_labels("pca64_kmeans"),
        "hdbscan_umap2d": load_labels("hdbscan_umap2d_mcs50"),
    }

    # ---------- stability fit functions ----------
    def fit_kmeans(idx):
        return KMeans(n_clusters=K, n_init=10,
                      random_state=SEED).fit_predict(X_pca[idx])

    def fit_hdbscan_umap(idx):
        return HDBSCAN(min_cluster_size=50,
                       metric="euclidean").fit_predict(XY[idx])

    fit_fns = {
        "pca64_kmeans": fit_kmeans,
        "hdbscan_umap2d": fit_hdbscan_umap,
    }

    # ---------- main comparison table ----------
    rows = []
    for name, labels in labelings.items():
        n_clusters = len([c for c in set(labels.tolist()) if c != -1])
        noise = float((labels == -1).mean())
        sil = silhouette_in_own_space(name, labels, X_pca, XY)

        Xe = euclidean_space(name, X_pca, XY)
        mask = labels != -1
        db = davies_bouldin_score(Xe[mask], labels[mask])
        ch = calinski_harabasz_score(Xe[mask], labels[mask])

        ari = adjusted_rand_score(existing, labels)
        nmi = normalized_mutual_info_score(existing, labels)
        ami = adjusted_mutual_info_score(existing, labels)

        if name in fit_fns:
            b_mean, b_std = bootstrap_ari(fit_fns[name], labels)
        else:
            b_mean, b_std = float("nan"), float("nan")

        stats_tbl, kw_stat, kw_p = cluster_statistics(df, labels, name)
        rows.append({
            "labeling": name, "n_clusters": n_clusters,
            "noise_frac": round(noise, 4), "silhouette": round(sil, 4),
            "davies_bouldin": round(db, 4), "calinski_harabasz": round(ch, 1),
            "ARI_vs_existing": round(ari, 4),
            "NMI_vs_existing": round(nmi, 4),
            "AMI_vs_existing": round(ami, 4),
            "bootstrap_ARI_mean": round(b_mean, 4),
            "bootstrap_ARI_std": round(b_std, 4),
            "kruskal_YM_p": f"{kw_p:.2e}",
        })
        print(f"[OK] {name}: ARI={ari:.3f} sil={sil:.3f} bootARI={b_mean:.3f} "
              f"KW_p={kw_p:.1e}")
        print(stats_tbl.to_string(index=False))

    table = pd.DataFrame(rows)
    table.to_csv(RESULTS_DIR / "comparison_table.csv", index=False)
    print("[OK] comparison_table.csv saved")
    print(table.to_string(index=False))

    # ---------- seed sensitivity ----------
    seed_rows = []
    base = labelings["pca64_kmeans"]
    for seed in range(10):
        lab = KMeans(n_clusters=K, n_init=10,
                     random_state=seed).fit_predict(X_pca)
        seed_rows.append(("pca64_kmeans", seed, adjusted_rand_score(base, lab)))
    umap_base = KMeans(n_clusters=K, n_init=10,
                       random_state=SEED).fit_predict(XY)
    for seed in (1, 7, 42):
        um = UMAP(n_components=2, n_neighbors=30, min_dist=0.1,
                  metric="euclidean", random_state=seed, n_jobs=1)
        XYs = um.fit_transform(X_pca)
        lab = KMeans(n_clusters=K, n_init=10, random_state=SEED).fit_predict(XYs)
        seed_rows.append(("umap2d_kmeans", seed, adjusted_rand_score(umap_base, lab)))
    pd.DataFrame(seed_rows, columns=["method", "seed", "ARI_vs_base"]).to_csv(
        RESULTS_DIR / "seed_stability.csv", index=False)
    print("[OK] seed_stability.csv saved")

    # ---------- figures ----------
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # UMAP scatter grid colored by each labeling
    n = len(labelings)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows),
                             dpi=300)
    axes = np.atleast_1d(axes).ravel()
    for ax, (name, labels) in zip(axes, labelings.items()):
        noise = labels == -1
        ax.scatter(XY[noise, 0], XY[noise, 1], c="lightgray", s=4, label="noise")
        ax.scatter(XY[~noise, 0], XY[~noise, 1], c=labels[~noise], s=4,
                   cmap="tab10")
        ari = adjusted_rand_score(existing, labels)
        ax.set_title(f"{name} (ARI={ari:.2f})", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    for ax in axes[n:]:
        ax.axis("off")
    fig.suptitle("Clusterings shown on UMAP-2D projection (color = cluster)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "umap_scatter_all_labelings.png", bbox_inches="tight")
    plt.close(fig)

    # contingency heatmaps vs existing
    names = [nm for nm in labelings if nm != "existing"]
    fig, axes = plt.subplots(1, len(names), figsize=(3.2 * len(names), 3.4),
                             dpi=300)
    for ax, name in zip(np.atleast_1d(axes).ravel(), names):
        ct = pd.crosstab(existing, labelings[name])
        ax.imshow(ct.values, cmap="Blues")
        ax.set_xticks(range(ct.shape[1]), ct.columns, fontsize=6)
        ax.set_yticks(range(ct.shape[0]), ct.index, fontsize=6)
        ax.set_xlabel(name, fontsize=8)
        ax.set_ylabel("existing", fontsize=8)
        for i in range(ct.shape[0]):
            for j in range(ct.shape[1]):
                if ct.values[i, j] > 0:
                    ax.text(j, i, ct.values[i, j], ha="center", va="center",
                            fontsize=6)
    fig.suptitle("Contingency: existing vs new clusterings")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "contingency_vs_existing.png", bbox_inches="tight")
    plt.close(fig)

    # metric bars
    t = table.set_index("labeling")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=300)
    t["silhouette"].plot.bar(ax=axes[0], color="steelblue")
    axes[0].set_title("Silhouette (own space)")
    t["ARI_vs_existing"].plot.bar(ax=axes[1], color="darkorange")
    axes[1].set_title("ARI vs existing")
    for ax in axes:
        ax.tick_params(axis="x", labelsize=8, rotation=30)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "metric_bars.png", bbox_inches="tight")
    plt.close(fig)

    print("[OK] Figures saved -> results/figures/")


if __name__ == "__main__":
    main()
