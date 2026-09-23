#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Group-aware RF hyperparameter selection.

Protocol: the production 96-combo grid is scored by GroupKFold(n_splits)
on `_fp_hash` (MD5 over the pooled Morgan fingerprint row), so identical
materials — same components at different ratios/crosslinking share
identical fingerprints — never straddle selection folds.

Deterministic by construction: GroupKFold is unshuffled and the RF seed is
fixed, so the same data always re-derives the same parameters. Tie rule:
the first combo in enumeration order wins.

Outputs (in --save_dir):
  best_params.json          {"best_params", "best_r2_gcv_mean", "protocol"}
  selection_landscape.csv   per-combo GroupKFold mean R2
"""
import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SEED = 42

# Production grid, verbatim (96 combinations).
RF_GRID = {
    "n_estimators": [300, 400, 600],
    "max_depth": [10, 15, 20, 25],
    "min_samples_split": [12, 16],
    "min_samples_leaf": [2, 4],
    "max_features": [0.1, 0.2],
}

def fp_hash_groups(feat_df: pd.DataFrame) -> np.ndarray:
    """Group key: MD5 over the fp_* row (float32 bytes), same rule as the
    classification pipeline. Identical fingerprints -> identical group."""
    fp_cols = [c for c in feat_df.columns if c.startswith("fp_")]
    return feat_df[fp_cols].apply(
        lambda r: hashlib.md5(
            r.values.astype(np.float32).tobytes()).hexdigest(), axis=1).values


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in_csv", required=True,
                    help="Pooled Morgan feature CSV (fp_* + target column)")
    ap.add_argument("--target", required=True)
    ap.add_argument("--save_dir", required=True)
    ap.add_argument("--n_splits", type=int, default=5)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.in_csv, low_memory=False)
    df = df.dropna(subset=[args.target]).reset_index(drop=True)
    fp_cols = [c for c in df.columns if c.startswith("fp_")]
    X = df[fp_cols].values.astype(np.float32)
    y = df[args.target].values.astype(np.float64)
    groups = fp_hash_groups(df)
    n_groups = pd.Series(groups).nunique()
    print(f"[INFO] rows={len(df)} fp={len(fp_cols)} groups={n_groups} "
          f"(duplicate rows: {len(df) - n_groups})")

    keys = list(RF_GRID)
    combos = [dict(zip(keys, v))
              for v in itertools.product(*(RF_GRID[k] for k in keys))]
    splits = list(GroupKFold(args.n_splits).split(X, y, groups=groups))
    print(f"[INFO] selecting over {len(combos)} combos x "
          f"GroupKFold({args.n_splits}) on _fp_hash")

    rows = []
    best, best_score = None, -np.inf
    for i, p in enumerate(combos, 1):
        scores = []
        for tr, va in splits:
            m = RandomForestRegressor(random_state=args.seed,
                                      n_jobs=-1, **p)
            m.fit(X[tr], y[tr])
            scores.append(r2_score(y[va], m.predict(X[va])))
        s = float(np.mean(scores))
        rows.append({"params": str(p), "R2_gcv_mean": round(s, 6)})
        # explicit tie rule: first in enumeration order wins
        if s > best_score + 1e-12:
            best, best_score = p, s
        if i % 12 == 0:
            print(f"[INFO]   {i}/{len(combos)} combos "
                  f"(best so far {best_score:.4f})")

    pd.DataFrame(rows).to_csv(save_dir / "selection_landscape.csv",
                              index=False, encoding="utf-8-sig")

    payload = {
        "best_params": best,
        "best_r2_gcv_mean": round(best_score, 6),
        "protocol": f"GroupKFold({args.n_splits}) on _fp_hash, "
                    f"production 96-combo grid, seed {args.seed}",
    }
    with open(save_dir / "best_params.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] selected params: {best} (GroupCV mean R2={best_score:.4f})")
    print(f"[OK] written: {save_dir / 'best_params.json'}")


if __name__ == "__main__":
    main()
