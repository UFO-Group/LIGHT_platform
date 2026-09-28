# -*- coding: utf-8 -*-
"""Phase A: run the honest pipeline end-to-end on the _add dataset and
compare against the production (base) run.

Reuses the production modules via subprocess (zero logic duplication):
  STEP0  main_regression/morgan_pooling.py        (radius 3 / alpha 3 / 1024)
  STEP1  main_regression/select_params_groupcv.py (GroupKFold(5) x 96 grid)
  STEP2  main_regression/deploy_rf.py             (honest GroupKFold(10) eval
         + full-data retrain + candidate prediction + final-10 self-check)
  STEP3  in-process comparison -> add_vs_base_summary.{md,json}

All outputs stay inside add_robustness/ (untracked sandbox). The tracked
legacy results/YoungsModulus_add/ and the production results/YoungsModulus/
are never touched.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REG = HERE.parents[1] / "Regression_Model"
MAIN = REG / "main_regression"
DATA = REG.parent / "DataBase"
HTP = REG.parent / "High-throughput predict"
PROD = REG / "results" / "YoungsModulus"

TARGET = "Young's Modulus (kPa) log10"
SR_PRED = (REG.parent / "Classification_Model" / "results"
           / "SwellingRatio" / "SwellingRatio_predict.csv")
SEED = 42

FEAT = HERE / "features" / "youngs_modulus_add-pooled-morgan.csv"
GRID = HERE / "rf_grid"
CV = HERE / "rf_cv10"
PRED = HERE / "predictions" / "RF_best_pred_kmeans_results.csv"


def run(cmd):
    print("\n====== RUN ======")
    print(" ".join(str(c) for c in cmd))
    print("=================\n")
    subprocess.run([str(c) for c in cmd], check=True)


def step0_pooling():
    if FEAT.exists() and FEAT.stat().st_size > 1024:
        print(f"[SKIP] features exist: {FEAT}")
        return
    run([sys.executable, MAIN / "morgan_pooling.py",
         "--in_csv", DATA / "youngs_modulus_add.csv",
         "--out_csv", FEAT,
         "--alpha", 3.0, "--radius", 3, "--nbits", 1024,
         "--polymer_cols", "SMILE A", "SMILE B", "SMILE C",
         "--target_col", TARGET])


def step1_selection():
    if (GRID / "best_params.json").exists():
        print(f"[SKIP] selection done: {GRID / 'best_params.json'}")
        return
    run([sys.executable, MAIN / "select_params_groupcv.py",
         "--in_csv", FEAT, "--target", TARGET,
         "--save_dir", GRID, "--n_splits", 5, "--seed", SEED])


def step2_deploy():
    if (CV / "fold_models" / "best_model.joblib").exists():
        print("[SKIP] deploy done")
        return
    PRED.parent.mkdir(parents=True, exist_ok=True)
    run([sys.executable, MAIN / "deploy_rf.py",
         "--in_csv", FEAT, "--target", TARGET,
         "--params_json", GRID / "best_params.json",
         "--save_dir", CV, "--honest_folds", 10, "--seed", SEED,
         "--predict_in_csv", HTP / "kmeans-pooled.csv",
         "--predict_source_csv", HTP / "kmeans_results.csv",
         "--pred_out_csv", PRED,
         "--sr_pred_csv", SR_PRED])


def step3_summary():
    base_params = json.load(open(PROD / "rf_grid" / "best_params.json",
                                 encoding="utf-8"))["best_params"]
    add_params = json.load(open(GRID / "best_params.json",
                                encoding="utf-8"))["best_params"]
    base_cv = pd.read_csv(PROD / "rf_cv10" / "cv10_metrics.csv")
    add_cv = pd.read_csv(CV / "cv10_metrics.csv")

    base_pred = pd.read_csv(PROD / "predictions"
                            / "RF_best_pred_kmeans_results.csv")
    add_pred = pd.read_csv(PRED)
    assert (base_pred["Pair_ID"].values == add_pred["Pair_ID"].values).all()
    rho = spearmanr(base_pred["RF_YoungsModulus_pred"],
                    add_pred["RF_YoungsModulus_pred"]).statistic
    dmax = float((base_pred["RF_YoungsModulus_pred"]
                 - add_pred["RF_YoungsModulus_pred"]).abs().max())

    report = (CV / "deploy_report.txt").read_text(encoding="utf-8-sig")
    sel_lines = [ln for ln in report.splitlines()
                 if "final selection" in ln or "reproduced" in ln
                 or "DIFFERS" in ln]

    summary = {
        "params": {"base": base_params, "add": add_params,
                   "identical": base_params == add_params},
        "honest_metrics": {
            "base": {"R2": round(base_cv["R2"].mean(), 4),
                     "R2_std": round(base_cv["R2"].std(), 4),
                     "RMSE": round(base_cv["RMSE"].mean(), 4),
                     "MAE": round(base_cv["MAE"].mean(), 4),
                     "rows": int(len(base_cv))},
            "add": {"R2": round(add_cv["R2"].mean(), 4),
                    "R2_std": round(add_cv["R2"].std(), 4),
                    "RMSE": round(add_cv["RMSE"].mean(), 4),
                    "MAE": round(add_cv["MAE"].mean(), 4),
                    "rows": int(len(add_cv))},
        },
        "candidates_630": {"spearman": round(float(rho), 4),
                           "max_abs_delta_pred": round(dmax, 4)},
        "final_selection_lines": sel_lines,
        "legacy_old_protocol_add": {"R2": 0.4948, "R2_std": 0.0803,
                                    "note": "old leaky protocol, NOT "
                                            "comparable; background only"},
    }
    with open(HERE / "add_vs_base_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    b, a = summary["honest_metrics"]["base"], summary["honest_metrics"]["add"]
    lines = [
        "# add 数据稳健性 —— 阶段 A(base vs base+32)概要",
        "",
        f"- 参数漂移:base {base_params}",
        f"  add  {add_params}",
        f"  identical = {summary['params']['identical']}",
        f"- 诚实指标(GroupKFold(10) per-fold 均值±std):",
        f"  base(1629 行): R2 = {b['R2']} ± {b['R2_std']}, "
        f"RMSE = {b['RMSE']}, MAE = {b['MAE']}",
        f"  add (1661 行): R2 = {a['R2']} ± {a['R2_std']}, "
        f"RMSE = {a['RMSE']}, MAE = {a['MAE']}",
        f"- 候选预测(630 对,base 模型 vs add 模型):"
        f"Spearman = {summary['candidates_630']['spearman']}, "
        f"max|Δpred| = {summary['candidates_630']['max_abs_delta_pred']}",
        "- 终选自检(deploy_report 原文):",
        *[f"  {ln}" for ln in sel_lines],
        "- 背景(旧泄漏协议 add 运行,口径不可比):"
        f"R2 = {summary['legacy_old_protocol_add']['R2']} "
        f"± {summary['legacy_old_protocol_add']['R2_std']}",
    ]
    (HERE / "add_vs_base_summary.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[OK] summary -> {HERE / 'add_vs_base_summary.md'}")


def main():
    step0_pooling()
    step1_selection()
    step2_deploy()
    step3_summary()


if __name__ == "__main__":
    main()
