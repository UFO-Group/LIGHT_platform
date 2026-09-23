#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Young's Modulus regression pipeline (one-click).

Protocol:

  STEP 1  Morgan pooling (radius/alpha/nbits pinned, defaults 3/3/1024)
  STEP 2  RF hyperparameter SELECTION by group-aware CV:
          main_regression/select_params_groupcv.py — production 96-combo
          grid scored with GroupKFold(n) on _fp_hash (MD5 of fingerprint
          row) so identical materials never straddle selection folds.
          Deterministic.
  STEP 3  DEPLOYMENT by main_regression/deploy_rf.py —
          a) honest evaluation: GroupKFold(10) on _fp_hash -> cv10_metrics.csv
          b) manufacturing: FULL-DATA retrain with selected params
          c) candidate prediction (schema consumed by the selection stage)
             + final-selection self-check replicating
             Agent/Selection_pipeline.py verbatim (report-only)
  STEP 4  model_candidates_for_llm.json (single RF entry, honest numbers)

Downstream consumers (API/advise_best_model_with_api.py, draw_pipline.py,
Agent/Selection_pipeline.py) keep their input files unchanged.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ===== Utilities =====
def run_cmd(cmd):
    print("\n====== RUN CMD ======")
    print(" ".join(cmd))
    print("=====================\n")
    subprocess.run(cmd, check=True)


def file_exists_and_valid(filepath: Path, min_size: int = 10) -> bool:
    """Check if file exists and is not empty."""
    if not filepath.exists():
        return False
    if not filepath.is_file():
        return False
    if filepath.stat().st_size < min_size:
        return False
    return True


def json_file_valid(filepath: Path) -> bool:
    """Check if JSON file exists and is valid."""
    if not file_exists_and_valid(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False


def csv_file_valid(filepath: Path, min_rows: int = 1) -> bool:
    if not file_exists_and_valid(filepath):
        return False
    try:
        df = pd.read_csv(filepath, nrows=5)
        return len(df) >= min_rows
    except Exception:
        return False


# ===== Wrappers =====
def run_morgan_pooling(main_dir: Path, raw_csv: str, out_csv: str,
                       polymer_cols, alpha: float, radius: int, nbits: int,
                       target_col: str = None):
    script = main_dir / "morgan_pooling.py"
    cmd = [
        sys.executable, str(script),
        "--in_csv", raw_csv,
        "--out_csv", out_csv,
        "--alpha", str(alpha),
        "--radius", str(radius),
        "--nbits", str(nbits),
    ]
    if polymer_cols:
        cmd += ["--polymer_cols", *polymer_cols]
    if target_col:
        cmd += ["--target_col", target_col]
    run_cmd(cmd)


def run_select_params(main_dir: Path, feat_csv: str, target_col: str,
                      save_dir: str, n_splits: int, seed: int):
    """STEP 2: deterministic group-aware hyperparameter selection."""
    script = main_dir / "select_params_groupcv.py"
    cmd = [
        sys.executable, str(script),
        "--in_csv", feat_csv,
        "--target", target_col,
        "--save_dir", save_dir,
        "--n_splits", str(n_splits),
        "--seed", str(seed),
    ]
    run_cmd(cmd)


def run_deploy(main_dir: Path, feat_csv: str, target_col: str,
               params_json: str, save_dir: str, honest_folds: int, seed: int,
               predict_in_csv: str = None, predict_source_csv: str = None,
               pred_out_csv: str = None, sr_pred_csv: str = None):
    """STEP 3: honest evaluation + full-data retrain + prediction +
    final-selection self-check."""
    script = main_dir / "deploy_rf.py"
    cmd = [
        sys.executable, str(script),
        "--in_csv", feat_csv,
        "--target", target_col,
        "--params_json", params_json,
        "--save_dir", save_dir,
        "--honest_folds", str(honest_folds),
        "--seed", str(seed),
    ]
    for a, v in (("--predict_in_csv", predict_in_csv),
                 ("--predict_source_csv", predict_source_csv),
                 ("--pred_out_csv", pred_out_csv),
                 ("--sr_pred_csv", sr_pred_csv)):
        if v:
            cmd += [a, v]
    run_cmd(cmd)


def write_candidates_json(out_root: Path, rf_cv_dir: Path,
                          pred_csv: Path, project_root: Path):
    """Single-RF candidates JSON for the advisory/draw steps (honest
    numbers; best_fold is diagnostic metadata only — the deployed model is a
    full-data retrain, not a fold model)."""
    metrics_file = rf_cv_dir / "cv10_metrics.csv"
    entry = {"model_type": "rf", "best_fold": None, "best_score": None,
             "pred_csv": None}
    if metrics_file.is_file():
        df = pd.read_csv(metrics_file)
        df.columns = [c.strip() for c in df.columns]
        if {"fold", "R2"}.issubset(df.columns):
            row = df.loc[df["R2"].idxmax()]
            entry["best_fold"] = int(row["fold"])
            entry["best_score"] = round(float(df["R2"].mean()), 4)
    if pred_csv is not None and pred_csv.exists():
        try:
            rel = pred_csv.resolve().relative_to(project_root)
            entry["pred_csv"] = "/" + str(rel).replace("\\", "/")
        except ValueError:
            entry["pred_csv"] = pred_csv.name
    json_path = out_root / "model_candidates_for_llm.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([entry], f, ensure_ascii=False, indent=2)
    print(f"[INFO] Written model candidate JSON: {json_path}")


# ===== Main Controller =====
def main():
    parser = argparse.ArgumentParser(
        description="One-Click: Morgan pooling + group-aware RF selection + "
                    "honest evaluation/full retrain + prediction + "
                    "final-selection self-check"
    )
    parser.add_argument("--raw_csv", required=True,
                        help="Raw training CSV (SMILES + target column)")
    parser.add_argument("--target", required=True,
                        help='Target column name')
    parser.add_argument("--out_root", required=True,
                        help="Root output directory")
    parser.add_argument("--polymer_cols", nargs="+",
                        default=["SMILE A", "SMILE B", "SMILE C"])
    parser.add_argument("--alpha", type=float, default=3.0,
                        help="morgan_pooling alpha, default 3.0")
    parser.add_argument("--radius", type=int, default=3,
                        help="Morgan radius, default 3")
    parser.add_argument("--nbits", type=int, default=1024,
                        help="Morgan fingerprint length, default 1024")
    parser.add_argument("--select_n_splits", type=int, default=5,
                        help="GroupKFold splits for selection, default 5")
    parser.add_argument("--honest_folds", type=int, default=10,
                        help="GroupKFold folds for honest evaluation, default 10")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip_existing", action="store_true", default=True)
    parser.add_argument("--force_rerun", action="store_true",
                        help="Force rerun all steps (overrides --skip_existing)")
    parser.add_argument("--do_predict", action="store_true",
                        help="Predict on candidates after deployment")
    parser.add_argument("--predict_in_csv",
                        help="Candidate feature CSV (e.g., kmeans-pooled.csv)")
    parser.add_argument("--predict_source_csv",
                        help="Candidate source CSV for merging output")
    parser.add_argument("--predict_target_name", default="Prediction",
                        help="Prediction column prefix, default Prediction")
    parser.add_argument("--sr_pred_csv",
                        help="SR classifier predictions for the final-selection "
                             "self-check (default: sibling Classification_Model "
                             "results path, if present)")
    args = parser.parse_args()

    if args.force_rerun:
        args.skip_existing = False
        print("[INFO] Force rerun mode enabled. Ignoring existing files.")

    ROOT = Path(__file__).resolve().parent
    MAIN_DIR = ROOT / "main_regression"
    if not args.sr_pred_csv:
        default_sr = (ROOT.parent / "Classification_Model" / "results"
                      / "SwellingRatio" / "SwellingRatio_predict.csv")
        args.sr_pred_csv = str(default_sr) if default_sr.exists() else None

    raw_csv_path = Path(args.raw_csv).resolve()
    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    feat_dir = out_root / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    feat_csv_path = feat_dir / (raw_csv_path.stem + "-pooled-morgan.csv")

    rf_grid_dir = out_root / "rf_grid"
    rf_cv_dir = out_root / "rf_cv10"
    rf_best_params_path = rf_grid_dir / "best_params.json"
    rf_best_model_path = rf_cv_dir / "fold_models" / "best_model.joblib"

    # ===== STEP 1: Morgan Fingerprint Generation =====
    print("\n===== [STEP 1] Generating Morgan Fingerprints =====")
    if args.skip_existing and file_exists_and_valid(feat_csv_path,
                                                    min_size=1024):
        print(f"[SKIP] Feature file exists: {feat_csv_path}")
    else:
        run_morgan_pooling(
            main_dir=MAIN_DIR,
            raw_csv=str(raw_csv_path),
            out_csv=str(feat_csv_path),
            polymer_cols=args.polymer_cols,
            alpha=args.alpha,
            radius=args.radius,
            nbits=args.nbits,
            target_col=args.target,
        )
    if not file_exists_and_valid(feat_csv_path):
        print(f"[ERROR] Feature file generation failed: {feat_csv_path}")
        sys.exit(1)

    # ===== STEP 2: Group-aware RF hyperparameter selection =====
    if args.skip_existing and json_file_valid(rf_best_params_path):
        print(f"\n===== [STEP 2] Valid RF best_params.json detected. "
              f"Skipping selection. =====")
        print(f"[SKIP] {rf_best_params_path}")
    else:
        print("\n===== [STEP 2] RF selection: GroupKFold on _fp_hash =====")
        run_select_params(
            main_dir=MAIN_DIR,
            feat_csv=str(feat_csv_path),
            target_col=args.target,
            save_dir=str(rf_grid_dir),
            n_splits=args.select_n_splits,
            seed=args.seed,
        )
    if not json_file_valid(rf_best_params_path):
        print("[ERROR] selection did not produce best_params.json")
        sys.exit(1)

    # ===== STEP 3: Honest evaluation + full retrain + prediction =====
    if args.skip_existing and file_exists_and_valid(rf_best_model_path):
        print(f"\n===== [STEP 3] Deployed RF model exists. Skipping. =====")
        print(f"[SKIP] {rf_best_model_path}")
    else:
        print("\n===== [STEP 3] RF deployment "
              "(honest eval + full retrain + predict + self-check) =====")
        extra = {}
        if args.do_predict:
            if not (args.predict_in_csv and args.predict_source_csv):
                print("[ERROR] --do_predict requires --predict_in_csv and "
                      "--predict_source_csv")
                sys.exit(1)
            predictions_dir = out_root / "predictions"
            predictions_dir.mkdir(parents=True, exist_ok=True)
            source_stem = Path(args.predict_source_csv).resolve().stem
            pred_out_csv_path = (predictions_dir /
                                 f"RF_best_pred_{source_stem}.csv")
            extra = dict(
                predict_in_csv=str(Path(args.predict_in_csv).resolve()),
                predict_source_csv=str(
                    Path(args.predict_source_csv).resolve()),
                pred_out_csv=str(pred_out_csv_path),
                sr_pred_csv=args.sr_pred_csv,
            )
        run_deploy(
            main_dir=MAIN_DIR,
            feat_csv=str(feat_csv_path),
            target_col=args.target,
            params_json=str(rf_best_params_path),
            save_dir=str(rf_cv_dir),
            honest_folds=args.honest_folds,
            seed=args.seed,
            **extra,
        )

    # ===== STEP 4: candidates JSON (advisory/draw inputs) =====
    print("\n===== [STEP 4] Writing model candidates JSON =====")
    source_for_pred = (Path(args.predict_source_csv).resolve()
                       if args.predict_source_csv else raw_csv_path)
    pred_path = (out_root / "predictions" /
                 f"RF_best_pred_{source_for_pred.stem}.csv")
    write_candidates_json(out_root, rf_cv_dir, pred_path, ROOT.parent)

    print("\n[DONE] Pipeline completed!")
    print(f"[DONE] Output root: {out_root}")

    print("\n" + "=" * 60)
    print("File Existence Check:")
    print("=" * 60)
    for name, path in [
        ("Morgan Feature File", feat_csv_path),
        ("RF Hyperparams File", rf_best_params_path),
        ("RF Deployed Model", rf_best_model_path),
        ("Honest Metrics", rf_cv_dir / "cv10_metrics.csv"),
        ("Deploy Report", rf_cv_dir / "deploy_report.txt"),
    ]:
        status = "✓ Exists" if file_exists_and_valid(path) else "✗ Missing"
        print(f"{name:20} {status:15} {path}")
    if args.do_predict:
        status = ("✓ Exists" if csv_file_valid(pred_path, min_rows=1)
                  else "✗ Missing")
        print(f"{'RF Prediction':20} {status:15} {pred_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
