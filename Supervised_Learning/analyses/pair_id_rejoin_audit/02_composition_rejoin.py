# -*- coding: utf-8 -*-
"""Composition-consistent recomputation of the final selection.

Ground truth established by 01 fingerprint arbitration (see README):
SwellingRatio_predict.csv's SMILE A/B is the TRUE composition of the
kmeans-pooled feature rows (630/630 fingerprint-identical); kmeans_results.csv
is misaligned (14/630). The production selection ran the material-family
regex filter on the YM side with the WRONG (kmeans) annotation and exported
those SMILES; band and class were per-feature-row and therefore correct.

This script redoes the Selection_pipeline rule with the TRUE annotation on
both sides:
  band   = production RF predictions (per Pair_ID, row-correct)
  class  = SR predictions (as production)
  regex  = clean_smiles_data applied to TRUE compositions on BOTH sides
  join   = Pair_ID (== feature row)
Outputs: corrected_selection.csv, rejoin_summary.json
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
YM_PRED = (REPO / "Supervised_Learning" / "Regression_Model" / "results"
           / "YoungsModulus" / "predictions" / "RF_best_pred_kmeans_results.csv")
SR_PRED = (REPO / "Supervised_Learning" / "Classification_Model" / "results"
           / "SwellingRatio" / "SwellingRatio_predict.csv")

MIN_YM, MAX_YM, TARGET_SR = 2.0, 3.3, 1
PRODUCTION_FINAL10 = ["Pair_1", "Pair_19", "Pair_37", "Pair_39", "Pair_41",
                      "Pair_44", "Pair_46", "Pair_53", "Pair_124", "Pair_229"]

SMILES_PATTERNS_TO_REMOVE = [
    r'O=C\(C\(C\[\*\]\)\s*\[\*\]\)N',
    r'\[\*\]OC1OC\(CO\)C\(OC2C\(O\)C\(O\)C\(\[\*\]\)C\(CO\)O2\)C\(O\)C1O'
]


def clean_smiles_data(df: pd.DataFrame, df_name: str) -> pd.DataFrame:
    """VERBATIM rule from Agent/Selection_pipeline.py:53-80."""
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


def main() -> None:
    ym = pd.read_csv(YM_PRED)
    sr = pd.read_csv(SR_PRED)

    # Replace the YM side's (wrong) kmeans annotation with the TRUE one.
    truth = sr[["Pair_ID", "SMILE A", "SMILE B"]]
    ym_true = ym.drop(columns=["SMILE A", "SMILE B"]).merge(
        truth, on="Pair_ID", how="left")

    ym_c = clean_smiles_data(ym_true, "YM (true annotation)")
    sr_c = clean_smiles_data(sr, "SR (true annotation)")
    band = ym_c[ym_c["RF_YoungsModulus_pred"].between(MIN_YM, MAX_YM)]
    cls = sr_c[sr_c["Prediction"] == TARGET_SR]
    merged = pd.merge(band, cls, on="Pair_ID", how="inner", suffixes=("", "_sr"))
    got = set(merged["Pair_ID"])
    expected = set(PRODUCTION_FINAL10)

    out_cols = ["Pair_ID", "SMILE A", "SMILE B", "row_index",
                "RF_YoungsModulus_pred", "Prediction",
                "Prediction_prob_class0", "Prediction_prob_class1"]
    merged[[c for c in out_cols if c in merged.columns]].to_csv(
        HERE / "corrected_selection.csv", index=False, encoding="utf-8-sig")

    summary = {
        "true_final": sorted(got, key=lambda s: int(s.split("_")[1])),
        "production_final10": PRODUCTION_FINAL10,
        "kept": sorted(expected & got, key=lambda s: int(s.split("_")[1])),
        "dropped": sorted(expected - got, key=lambda s: int(s.split("_")[1])),
        "added": sorted(got - expected, key=lambda s: int(s.split("_")[1])),
        "n_band_after_true_regex": int(len(band)),
        "n_class1_after_regex": int(len(cls)),
    }
    with open(HERE / "rejoin_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # For the production 10: the true compositions (what the wet lab should
    # have seen) vs what the exported CSV showed (kmeans annotation).
    km = pd.read_csv(REPO / "Supervised_Learning" / "High-throughput predict"
                     / "kmeans_results.csv").rename(
        columns={"SMILE_A": "SMILE A", "SMILE_B": "SMILE B"})
    rows = []
    for pid in PRODUCTION_FINAL10:
        shown = km[km["Pair_ID"] == pid][["SMILE A", "SMILE B"]].iloc[0]
        real = truth[truth["Pair_ID"] == pid][["SMILE A", "SMILE B"]].iloc[0]
        same = (set(shown) == set(real))
        rows.append({"Pair_ID": pid, "exported_was_correct": bool(same),
                     "true_SMILE_A": real["SMILE A"], "true_SMILE_B": real["SMILE B"]})
    pd.DataFrame(rows).to_csv(HERE / "final10_true_compositions.csv",
                              index=False, encoding="utf-8-sig")
    print(f"[OK] final10_true_compositions.csv | "
          f"exported correct: {sum(r['exported_was_correct'] for r in rows)}/10")


if __name__ == "__main__":
    main()
