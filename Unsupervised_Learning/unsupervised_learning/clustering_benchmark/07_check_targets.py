# -*- coding: utf-8 -*-
"""Check whether the 10 LLM-screened target formulas survive re-clustering.

Pipeline context: the existing pipeline clustered the 1291-row dataset
(UMAP-2D + KMeans k=6), took the best cluster (cluster 3, 68 rows, 36
unique materials), formed all C(36,2)=630 pairwise material combinations,
predicted each pair with the supervised model, and an LLM consensus screen
kept 10 formulas (see LLM_consensus/database/formula_materials.json).

This script replays the candidate-set construction under each labeling:
best cluster (argmax prob_SR, size >= 30) -> unique material set -> all
pairs. A formula is IN iff both of its component material SMILES are in
that set. Also prints a per-material cluster map for diagnostics.

The 10 formulas and their material names are hardcoded (source: the
candidate csv NAME columns).
"""
import sys
from pathlib import Path

import pandas as pd

from common import RESULTS_DIR, SMILE_COLS, load_labels, load_source, \
    rebuild_existing_labels

# label name -> (labels handle, statistics csv)
METHODS = {
    "existing": (None, "cluster_statistics_existing.csv"),
    "pca64_kmeans": ("pca64_kmeans", "cluster_statistics_pca64_kmeans.csv"),
    "hdbscan_umap2d": ("hdbscan_umap2d_mcs50",
                       "cluster_statistics_hdbscan_umap2d.csv"),
}

# target.md formulas -> candidate-csv NAME keys (substring match)
FORMULAS = {
    1: ("Gelatin(Gel)", "Gelatin_methacrylate(GelMA)"),
    2: ("Polyacrylamide(PAM)", "Gelatin(Gel)"),
    3: ("Chitosan", "Gelatin_methacrylate(GelMA)"),
    4: ("Gelatin_methacrylate(GelMA)", "Silk"),
    5: ("Gelatin_methacrylate(GelMA)", "PEG"),
    6: ("Starch", "Gelatin_methacrylate(GelMA)"),
    7: ("Chitin", "Gelatin_methacrylate(GelMA)"),
    8: ("Gelatin_methacrylate(GelMA)", "Cellulose"),
    9: ("Polyacrylamide(PAM)", "PVA"),
    10: ("Polyacrylamide(PAM)", "PEG"),
}

MIN_BEST_SIZE = 30  # ignore degenerate clusters when picking the best


def main():
    df, _ = load_source()
    cand = pd.read_csv(Path(__file__).resolve().parent.parent.parent
                       / "candidate_umap" / "Prediction-1028-ALL2-candidate.csv")

    # name -> SMILES vocabulary from candidate csv (both A and B sides)
    vocab = {}
    for side in ("A", "B"):
        for name, smi in zip(cand[f"NAME {side}"], cand[f"SMILE {side}"]):
            vocab[str(name).strip()] = str(smi).strip()

    resolved = {}
    for fid, (n1, n2) in FORMULAS.items():
        s1 = next((v for k, v in vocab.items() if n1 in k), None)
        s2 = next((v for k, v in vocab.items() if n2 in k), None)
        assert s1 and s2, f"formula {fid} unresolved: {n1!r}/{n2!r}"
        resolved[fid] = (s1, s2)
    target_mats = sorted({s for pair in resolved.values() for s in pair})
    print(f"[OK] {len(target_mats)} distinct target-material SMILES resolved")

    # row SMILE sets
    sets = [set() for _ in range(len(df))]
    for i, row in df.iterrows():
        for c in SMILE_COLS:
            v = row[c]
            if pd.notna(v) and str(v).strip():
                sets[i].add(str(v).strip())

    labelings = {"existing": rebuild_existing_labels(df)}
    for m, (ln, _) in METHODS.items():
        if ln:
            labelings[m] = load_labels(ln)

    best, matsets = {}, {}
    for m, (_, sf) in METHODS.items():
        st = pd.read_csv(RESULTS_DIR / sf)
        top = st[st["size"] >= MIN_BEST_SIZE].sort_values(
            "prob_SR", ascending=False).iloc[0]
        best[m] = int(top["cluster"])
        labels = labelings[m]
        mset = set()
        for i in range(len(df)):
            if labels[i] == best[m]:
                mset |= sets[i]
        matsets[m] = mset
        print(f"[OK] {m}: best={best[m]} size={int(top['size'])} "
              f"prob_SR={top['prob_SR']:.4f} prob_YM={top['prob_YM']:.4f} "
              f"| unique materials={len(mset)} pairs={len(mset)*(len(mset)-1)//2}")

    print("\n===== VERDICT (IN = both materials in method's best cluster) =====")
    rows_out = []
    for fid in sorted(FORMULAS):
        s1, s2 = resolved[fid]
        rec = {"formula": f"F{fid}"}
        for m in METHODS:
            rec[m] = "IN" if (s1 in matsets[m] and s2 in matsets[m]) else "OUT"
        rows_out.append(rec)
    out = pd.DataFrame(rows_out)
    print(out.to_string(index=False))

    print("\n===== MATERIAL DETAIL (clusters of rows containing each material; * marks method best) =====")
    det_rows = []
    for smi in target_mats:
        name = next(k for k, v in vocab.items() if v == smi)
        idxs = [i for i in range(len(df)) if smi in sets[i]]
        rec = {"material": name[:28], "n_rows": len(idxs)}
        for m in METHODS:
            labels = labelings[m]
            cl = sorted({int(labels[i]) for i in idxs if labels[i] != -1})
            noise = sum(1 for i in idxs if labels[i] == -1)
            mark = "*" if best[m] in cl else " "
            rec[m] = f"{mark}{cl}" + (f"(n{noise})" if noise else "")
        det_rows.append(rec)
    detail = pd.DataFrame(det_rows)
    print(detail.to_string(index=False))

    out.to_csv(RESULTS_DIR / "check_targets.csv", index=False,
               encoding="utf-8-sig")
    detail.to_csv(RESULTS_DIR / "check_targets_materials.csv", index=False,
                  encoding="utf-8-sig")
    print("\n[OK] saved -> results/check_targets.csv, "
          "results/check_targets_materials.csv")


if __name__ == "__main__":
    sys.exit(main())
