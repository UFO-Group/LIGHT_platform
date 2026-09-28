#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy the RF regression head: honest evaluation, full-data retrain,
candidate prediction, and final-selection self-check.

Manufacturing: the deployed model is retrained on ALL training rows with the
group-selected parameters (no fold model is shipped).

Honest reporting: GroupKFold(honest_folds) on `_fp_hash`, R2/RMSE/MAE per
fold + mean +- std -> cv10_metrics.csv. CAVEAT (also written to
deploy_report.txt): the selected parameters were chosen on the same dataset
(one-shot group selection), so the honest-fold scores are mildly optimistic.

Final-selection self-check: replicates Agent/Selection_pipeline.py VERBATIM
(SMILES-pattern cleaning + 2.0 <= YM <= 3.3 AND Prediction == 1 + inner join
on Pair_ID) on the freshly predicted candidates, then reports
kept/dropped/added against EXPECTED_FINAL10. Report-only by design: with the
current data the selection is reproduced exactly; if the training data or
candidates change, a differing selection is legitimate but MUST be visible,
so it is printed and written to deploy_report.txt.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from select_params_groupcv import fp_hash_groups

SEED = 42
MIN_YM, MAX_YM, TARGET_SR = 2.0, 3.3, 1  # Selection_pipeline.py:153-157 verbatim

EXPECTED_FINAL10 = [
    "Pair_1", "Pair_19", "Pair_37", "Pair_39", "Pair_41",
    "Pair_44", "Pair_46", "Pair_53", "Pair_124", "Pair_229",
]


def clean_smiles_data(df: pd.DataFrame, df_name: str) -> pd.DataFrame:
    """VERBATIM copy of Agent/Selection_pipeline.py:53-80 (patterns, columns,
    behaviour) so the self-check matches the real selection stage exactly."""
    SMILES_PATTERNS_TO_REMOVE = [
        r'O=C\(C\(C\[\*\]\)\s*\[\*\]\)N',
        r'\[\*\]OC1OC\(CO\)C\(OC2C\(O\)C\(O\)C\(\[\*\]\)C\(CO\)O2\)C\(O\)C1O'
    ]
    mask = pd.Series([False] * len(df), index=df.index)
    smiles_cols = [c for c in ["SMILE A", "SMILE B"] if c in df.columns]
    if not smiles_cols:
        print(f"[WARN] '{df_name}' missing SMILE columns; cleaning skipped.")
        return df
    for pattern in SMILES_PATTERNS_TO_REMOVE:
        for col in smiles_cols:
            mask |= df[col].astype(str).str.contains(pattern, na=False,
                                                     regex=True)
    return df[~mask].copy()


def metrics(y: np.ndarray, p: np.ndarray) -> tuple:
    r2 = 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return (float(r2), float(np.sqrt(((y - p) ** 2).mean())),
            float(np.abs(y - p).mean()))


def load_params(params_json: Path) -> dict:
    with open(params_json, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return obj.get("best_params", obj)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--params_json", required=True)
    ap.add_argument("--save_dir", required=True,
                    help="e.g. results/YoungsModulus/rf_cv10")
    ap.add_argument("--model_subdir", default="fold_models")
    ap.add_argument("--predict_in_csv",
                    help="Candidate feature CSV (e.g. kmeans-pooled.csv)")
    ap.add_argument("--predict_source_csv",
                    help="Candidate source CSV with Pair_ID + SMILE_A/SMILE_B")
    ap.add_argument("--pred_out_csv")
    ap.add_argument("--sr_pred_csv",
                    help="SR classifier predictions (Pair_ID + Prediction) "
                         "for the final-selection self-check")
    ap.add_argument("--honest_folds", type=int, default=10)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    report: list = []

    def say(s: str = ""):
        print(s)
        report.append(s)

    def rel(p) -> str:
        """Report paths relative to the working directory when possible."""
        try:
            return str(Path(p).resolve().relative_to(Path.cwd()))
        except ValueError:
            return str(p)

    params = load_params(Path(args.params_json))
    say(f"[INFO] params (from {rel(args.params_json)}): {params}")

    df = pd.read_csv(args.in_csv, low_memory=False)
    df = df.dropna(subset=[args.target]).reset_index(drop=True)
    fp_cols = [c for c in df.columns if c.startswith("fp_")]
    X = df[fp_cols].values.astype(np.float32)
    y = df[args.target].values.astype(np.float64)
    groups = fp_hash_groups(df)

    # ---- honest evaluation: GroupKFold on _fp_hash -------------------------
    rows = []
    for i, (tr, te) in enumerate(
            GroupKFold(args.honest_folds).split(X, y, groups=groups), 1):
        m = RandomForestRegressor(random_state=args.seed, n_jobs=-1,
                                  **params)
        m.fit(X[tr], y[tr])
        r2, rmse_v, mae_v = metrics(y[te], m.predict(X[te]))
        rows.append({"fold": i, "R2": round(r2, 4),
                     "RMSE": round(rmse_v, 4), "MAE": round(mae_v, 4),
                     "n_test": int(len(te))})
    met = pd.DataFrame(rows)
    met.to_csv(save_dir / "cv10_metrics.csv", index=False,
               encoding="utf-8-sig")
    say(f"[OK] honest metrics (GroupKFold({args.honest_folds}) on _fp_hash): "
        f"R2 = {met['R2'].mean():.3f} ± {met['R2'].std():.3f} | "
        f"RMSE = {met['RMSE'].mean():.3f} | MAE = {met['MAE'].mean():.3f}")
    say("[NOTE] caveat: hyperparameters were selected on the same dataset "
        "(GroupKFold(5)); GroupKFold(10) scores are therefore mildly "
        "optimistic.")

    # ---- manufacturing: full-data retrain ----------------------------------
    model_dir = save_dir / args.model_subdir
    model_dir.mkdir(parents=True, exist_ok=True)
    model = RandomForestRegressor(random_state=args.seed, n_jobs=-1,
                                  **params).fit(X, y)
    dump(model, model_dir / "best_model.joblib")
    say(f"[OK] deployed model (full-data retrain, {len(df)} rows) -> "
        f"{rel(model_dir / 'best_model.joblib')}")

    # ---- candidate prediction (schema consumed by the selection stage) ----
    if args.predict_in_csv and args.predict_source_csv and args.pred_out_csv:
        cand = pd.read_csv(args.predict_in_csv, low_memory=False)
        assert fp_cols == [c for c in cand.columns if c.startswith("fp_")], \
            "fp column mismatch between training and candidate features"
        src = pd.read_csv(args.predict_source_csv, low_memory=False)
        assert len(cand) == len(src), "candidate feature/source row mismatch"
        pred = model.predict(cand[fp_cols].values.astype(np.float32))
        out = pd.DataFrame({
            "Pair_ID": src["Pair_ID"].values,
            "SMILE A": src["SMILE_A"].values,
            "SMILE B": src["SMILE_B"].values,
            "row_index": np.arange(len(src)),
            "RF_YoungsModulus_pred": pred,
        })
        out.to_csv(args.pred_out_csv, index=False, encoding="utf-8-sig")
        say(f"[OK] predictions ({len(out)} candidates) -> "
            f"{rel(args.pred_out_csv)}")

        # ---- final-selection self-check (Selection_pipeline verbatim) ------
        if args.sr_pred_csv:
            sr = pd.read_csv(args.sr_pred_csv, low_memory=False)
            ym = clean_smiles_data(out, "YoungsModulus Data")
            sr_clean = clean_smiles_data(sr, "SwellingRatio Data")
            band = ym[ym["RF_YoungsModulus_pred"].between(MIN_YM, MAX_YM)]
            cls = sr_clean[sr_clean["Prediction"] == TARGET_SR]
            merged = pd.merge(band, cls, on="Pair_ID", how="inner")
            got = set(merged["Pair_ID"])
            expected = set(EXPECTED_FINAL10)
            say("---- final-selection self-check "
                "(Selection_pipeline.py rule, verbatim) ----")
            say(f"final selection: {len(got)} pairs | "
                f"kept {len(got & expected)}/10 | "
                f"dropped {sorted(expected - got)} | "
                f"added {sorted(got - expected)}")
            if got == expected:
                say("[OK] final selection reproduced exactly (10/10).")
            else:
                say("[WARNING] final selection DIFFERS from the expected "
                    "list. If training data or candidates changed this may "
                    "be legitimate — re-verify before any deployment claim.")

    (save_dir / "deploy_report.txt").write_text(
        "\n".join(report), encoding="utf-8-sig")
    print(f"[OK] report -> {save_dir / 'deploy_report.txt'}")


if __name__ == "__main__":
    main()
