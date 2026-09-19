# -*- coding: utf-8 -*-
"""Prepare the ADDED dataset for the clustering benchmark (supplementary).

Source of truth: clusters_add/cluster_0..5.csv (1303 rows total) — the merged
output of the manual `_add` run. These files already contain the joined
Swelling Ratio / YM(kPa) columns, and the file split encodes the existing
K=6 labels, so labels are trivially recoverable (label = file index).

Fingerprints are regenerated with the exact protocol of morgan.py:
standardize SMILES -> Morgan count FP (radius=2, 1024, count) for SMILE A/B
-> average pooling.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
UL_DIR = BASE_DIR.parent                  # unsupervised_learning/
LIB_DIR = UL_DIR.parent                   # Unsupervised_Learning/ (morgan_pooling.py)
RESULTS_ADD = BASE_DIR / "results_add"
CLUSTERS_ADD = UL_DIR / "clusters_add"
K = 6

sys.path.append(str(LIB_DIR))
from morgan_pooling import _SmilesStandardizer, build_morgan_generator, morgan_from_smi  # noqa: E402


def main():
    frames = []
    labels = []
    for lbl in range(K):
        cdf = pd.read_csv(CLUSTERS_ADD / f"cluster_{lbl}.csv", encoding="utf-8-sig")
        frames.append(cdf)
        labels.extend([lbl] * len(cdf))
        print(f"[OK] cluster_{lbl}.csv: {len(cdf)} rows")

    df = pd.concat(frames, ignore_index=True)
    labels = np.array(labels, dtype=np.int64)
    print(f"[OK] Merged added dataset: {df.shape}")

    RESULTS_ADD.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_ADD / "source_add.csv", index=False, encoding="utf-8-sig")
    np.save(RESULTS_ADD / "labels_existing_add.npy", labels)

    # ---- regenerate fingerprints (morgan.py protocol) ----
    gen = build_morgan_generator(
        radius=2,
        fp_size=1024,
        use_chirality=False,
        use_features=False,
        use_bond_types=True,
        include_ring=False,
    )
    std = _SmilesStandardizer(use_std=True)

    fps = []
    n_fail = 0
    for _, row in df.iterrows():
        smi_a = std.canonical_smiles(str(row.get("SMILE A", "")))
        smi_b = std.canonical_smiles(str(row.get("SMILE B", "")))
        fp_a = morgan_from_smi(smi_a, gen, nbits=1024, fp_type="count")
        fp_b = morgan_from_smi(smi_b, gen, nbits=1024, fp_type="count")
        if fp_a is None or fp_b is None:
            n_fail += 1
        fps.append((np.asarray(fp_a, dtype=np.float32)
                    + np.asarray(fp_b, dtype=np.float32)) / 2.0)

    X = np.array(fps, dtype=np.float32)
    np.save(RESULTS_ADD / "AB_concat1024_add.npy", X)
    print(f"[OK] Fingerprints: {X.shape}, failed rows: {n_fail}")
    print("[OK] Saved -> results_add/{source_add.csv, labels_existing_add.npy, "
          "AB_concat1024_add.npy}")


if __name__ == "__main__":
    main()
