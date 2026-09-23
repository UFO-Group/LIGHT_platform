#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Young's Modulus Analysis Pipeline
- Step1: regression_main.py
- Step2: check model_candidates_for_llm.json
- Step3: advise_best_model_with_api.py
- Step4: draw_pipline.py (Plot scatter plots for the best R2 fold of each model)
"""

import subprocess
import sys
import json
from pathlib import Path


def run_regression(cwd: Path):
    """Run regression analysis"""
    print("=== Running Regression Analysis ===")

    cmd = [
        sys.executable, "regression_main.py",
        "--raw_csv", "../DataBase/youngs_modulus.csv",
        "--target", "Young's Modulus (kPa) log10",
        "--out_root", "results/YoungsModulus",
        "--polymer_cols", "SMILE A", "SMILE B", "SMILE C",
        "--do_predict",
        "--predict_in_csv", "../High-throughput predict/kmeans-pooled.csv",
        "--predict_source_csv", "../High-throughput predict/kmeans_results.csv",
        "--predict_target_name", "YoungsModulus_pred"
    ]

    print(f"Executing command: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(cwd))


def check_candidates_file(cwd: Path):
    """Check if the candidate models file exists and is valid"""
    candidates_path = cwd / "results" / "YoungsModulus" / "model_candidates_for_llm.json"

    if not candidates_path.exists():
        print(f"File not found: {candidates_path}")
        return False

    if candidates_path.stat().st_size == 0:
        print(f"File is empty: {candidates_path}")
        return False

    try:
        with open(candidates_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            print("Error: JSON file does not contain a valid list of candidate models")
            return False

        print(f"Found {len(data)} candidate models")
        return True

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False


def run_advise(cwd: Path):
    """Run model recommendation"""
    print("=== Running Model Recommendation ===")

    cmd = [
        sys.executable, "API/advise_best_model_with_api.py",
        "--candidates_json", "results/YoungsModulus/model_candidates_for_llm.json",
        "--out_json", "results/YoungsModulus/overall_best_model.json"
    ]

    print(f"Executing command: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(cwd))


def run_draw_pipeline(cwd: Path):
    """Run plotting: Plot scatter graph for the fold with max R2 for each model"""
    print("=== Plotting scatter graphs for best R2 fold of each model ===")

    out_root = "results/YoungsModulus"
    cmd = [
        sys.executable, "draw_pipline.py",
        "--out_root", out_root,
        "--only", "all"
    ]

    print(f"Executing command: {' '.join(cmd)}")
    # Failure in plotting shouldn't block the main flow; change check=True to enforce strict failure
    return subprocess.run(cmd, cwd=str(cwd))

def check_draw_results(draw_root: Path):
    """
    Check if scatter plots already exist for rf
    (the pipeline deploys RF only; other model families are compared in
    separate analyses, not in this runtime pipeline.)
    Returns (all_exist: bool, detail: dict)
    detail: {
        "rf": [Path, ...],
    }
    """
    models = ["rf"]
    detail = {}
    all_exist = True

    for m in models:
        pattern = draw_root / m / "fold_*" / "scatter_*.png"
        files = list(draw_root.glob(f"{m}/fold_*/scatter_*.png"))
        detail[m] = files
        if not files:
            all_exist = False

    return all_exist, detail


def main():
    cwd = Path(__file__).parent.resolve()

    # Step1: Regression Analysis
    result = run_regression(cwd)
    if result.returncode != 0:
        print("Error: Regression analysis failed")
        sys.exit(1)

    # Step2: Check Candidates
    if not check_candidates_file(cwd):
        print("Error: Invalid candidate models file, skipping model selection")
        sys.exit(1)

    # Step3: LLM/API Recommendation
    result = run_advise(cwd)
    if result.returncode != 0:
        print("Error: Model recommendation failed")
        sys.exit(1)

    # Step4: Check and Draw (Skip if already exists)
    draw_root = cwd / "results" / "YoungsModulus" / "draw"
    
    all_exist, detail = check_draw_results(draw_root)
    
    if all_exist:
        print("\n=== Plotting results already exist, skipping draw_pipline ===")
        for model, files in detail.items():
            print(f"[OK] {model.upper()} scatter plot exists:")
            for p in files:
                print(f"     - {p}")
    else:
        print("\n=== Missing scatter plots detected, starting plotting ===")
        for model, files in detail.items():
            if not files:
                print(f"[MISS] {model.upper()} scatter plot missing, will generate")
            else:
                print(f"[OK]   {model.upper()} has scatter plots, count={len(files)}")
    
        result = run_draw_pipeline(cwd)
        if result.returncode != 0:
            print("[WARN] Plotting step failed (does not affect main flow), please check draw_pipline output logs.")

    print("=== All steps completed ===")


if __name__ == "__main__":
    main()