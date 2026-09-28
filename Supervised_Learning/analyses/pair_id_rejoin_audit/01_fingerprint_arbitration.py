# -*- coding: utf-8 -*-
"""Fingerprint arbitration: which candidate-file annotation matches the
kmeans-pooled feature rows?

Two files annotate the same 630 feature rows with compositions:
  - High-throughput predict/kmeans_results.csv     (SMILE_A/SMILE_B)
  - Classification_Model SwellingRatio_predict.csv (SMILE A/SMILE B)
They disagree on 617/630 Pair_IDs. This script re-pools BOTH annotations
with the production parameters (alpha 3 / radius 3 / 1024 bits,
polymer cols A+B) and compares fingerprints row-by-row against
kmeans-pooled.csv. The annotation with 630/630 identical rows is the
true composition of the feature rows.

Output: arbitration_summary.json (+ tmp/ intermediates, cleaned).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
HTP = (HERE.parents[1] / "High-throughput predict")
SR_PRED = (HERE.parents[1] / "Classification_Model" / "results"
           / "SwellingRatio" / "SwellingRatio_predict.csv")
POOLING = (HERE.parents[1] / "Regression_Model" / "main_regression"
           / "morgan_pooling.py")


def pool(tag: str, df: pd.DataFrame) -> pd.DataFrame:
    src = HERE / "tmp" / f"annot_{tag}.csv"
    out = HERE / "tmp" / f"pooled_{tag}.csv"
    df.to_csv(src, index=False)
    subprocess.run([sys.executable, str(POOLING),
                    "--in_csv", str(src), "--out_csv", str(out),
                    "--alpha", "3.0", "--radius", "3", "--nbits", "1024",
                    "--polymer_cols", "SMILE A", "SMILE B"],
                   check=True, capture_output=True)
    return pd.read_csv(out, low_memory=False)


def main() -> None:
    tmp = HERE / "tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    ref = pd.read_csv(HTP / "kmeans-pooled.csv", low_memory=False)
    fp_ref = ref[[c for c in ref.columns if c.startswith("fp_")]].values
    km = pd.read_csv(HTP / "kmeans_results.csv").rename(
        columns={"SMILE_A": "SMILE A", "SMILE_B": "SMILE B"})
    sr = pd.read_csv(SR_PRED)

    out = {}
    for tag, df in (("kmeans_results", km[["Pair_ID", "SMILE A", "SMILE B"]]),
                    ("SwellingRatio_predict", sr[["Pair_ID", "SMILE A", "SMILE B"]])):
        p = pool(tag, df)
        fpc = [c for c in p.columns if c.startswith("fp_")]
        d = np.abs(p[fpc].values.astype(np.float32)
                   - fp_ref.astype(np.float32)).sum(axis=1)
        out[tag] = {"fingerprint_identical_rows": int((d == 0).sum()),
                    "total_rows": int(len(d))}
        print(f"[{tag}] fingerprint-identical rows: "
              f"{out[tag]['fingerprint_identical_rows']}/{len(d)}")

    truth = max(out, key=lambda k: out[k]["fingerprint_identical_rows"])
    out["verdict_true_annotation"] = truth
    shutil.rmtree(tmp)
    with open(HERE / "arbitration_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[VERDICT] true composition annotation = {truth}")


if __name__ == "__main__":
    main()
