# -*- coding: utf-8 -*-
"""Phase B: paired selection-drift test on the _add dataset.

Same GroupKFold(10) folds on _fp_hash as the deploy stage; two configs
evaluated pairwise per fold:
  (i)  frozen base params   (production rf_grid/best_params.json)
  (ii) re-selected add params (add_robustness/rf_grid/best_params.json)

Wilcoxon signed-rank over the 10 paired fold R2 differences.
Degrade path (plan: fallback to Phase A): if the two configs are identical
or the differences are degenerate, report mean diff + note; Phase A's
summary is unaffected.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(HERE.parents[1] / "Regression_Model"
                       / "main_regression"))
from select_params_groupcv import fp_hash_groups  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REG = HERE.parents[1] / "Regression_Model"
PROD = REG / "results" / "YoungsModulus"
TARGET = "Young's Modulus (kPa) log10"
SEED = 42

FEAT = HERE / "features" / "youngs_modulus_add-pooled-morgan.csv"


def main():
    frozen = json.load(open(PROD / "rf_grid" / "best_params.json",
                            encoding="utf-8"))["best_params"]
    reselected = json.load(open(HERE / "rf_grid" / "best_params.json",
                                encoding="utf-8"))["best_params"]

    df = pd.read_csv(FEAT, low_memory=False)
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)
    fp_cols = [c for c in df.columns if c.startswith("fp_")]
    X = df[fp_cols].values.astype(np.float32)
    y = df[TARGET].values.astype(np.float64)
    groups = fp_hash_groups(df)
    print(f"[INFO] rows={len(df)} fp={len(fp_cols)} "
          f"groups={pd.Series(groups).nunique()}")

    out = {"frozen_params": frozen, "reselected_params": reselected,
           "identical_params": frozen == reselected}

    if frozen == reselected:
        out["verdict"] = ("selected params identical on base and add data; "
                          "paired test moot (zero drift by construction)")
        print("[OK] params identical -> no drift to test")
    else:
        r2_f, r2_r = [], []
        for tr, te in GroupKFold(10).split(X, y, groups=groups):
            mf = RandomForestRegressor(random_state=SEED, n_jobs=-1,
                                       **frozen).fit(X[tr], y[tr])
            mr = RandomForestRegressor(random_state=SEED, n_jobs=-1,
                                       **reselected).fit(X[tr], y[tr])
            r2_f.append(r2_score(y[te], mf.predict(X[te])))
            r2_r.append(r2_score(y[te], mr.predict(X[te])))
        d = np.array(r2_r) - np.array(r2_f)
        out["fold_R2_frozen"] = [round(v, 4) for v in r2_f]
        out["fold_R2_reselected"] = [round(v, 4) for v in r2_r]
        out["diff_mean"] = float(d.mean())
        out["diff_std"] = float(d.std())
        try:
            stat, p = wilcoxon(d)
            out["wilcoxon_stat"], out["wilcoxon_p"] = float(stat), float(p)
            out["verdict"] = (f"mean diff {d.mean():+.4f} "
                              f"(Wilcoxon p={p:.3f})")
        except ValueError:
            out["verdict"] = (f"degenerate differences (mean {d.mean():+.4f});"
                              " no significant test possible — Phase A "
                              "comparison stands alone")
        print(f"[frozen ] mean R2 = {np.mean(r2_f):.4f}")
        print(f"[reselect] mean R2 = {np.mean(r2_r):.4f}")
        print(f"[verdict] {out['verdict']}")

    with open(HERE / "paired_drift.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[OK] -> {HERE / 'paired_drift.json'}")


if __name__ == "__main__":
    main()
