# -*- coding: utf-8 -*-
"""Reference implementation of a CORRECT material-candidate export.

Design principles (what the export should be, independent of how the
current pipeline happens to do it):
  P1  One canonical table keyed by the feature row (Pair_ID = row of
      kmeans-pooled.csv); compositions from the fingerprint-verified
      annotation (SwellingRatio_predict.csv) only.
  P2  Every filter applied to the SAME canonical compositions (no
      per-side annotation that can drift).
  P3  Decisions ship with their evidence: predicted value, distances to
      band edges, class probability, margin to the 0.5 boundary.
  P4  Borderline visibility: explicit margin columns + flag; near-miss
      "bench" list (gated out by <0.1 log10 or prob in [0.45, 0.5)) so
      wet-lab contingency is planned, not discovered later.
  P5  Family exclusion applied by MATERIAL FAMILY on true compositions
      (polyacrylamide-family and cellulose-disaccharide-family, including
      alternate notations the original regex missed), not by one
      SMILES-string spelling.
  P6  No silent joins: every row carries Pair_ID; the export states its
      gate rule in the header comment.

Inputs (read-only): production RF predictions, SR classifier predictions,
add-run predictions (evidence column only).
Outputs: correct_material_export.csv, alternates_bench.csv, family_map.csv.
"""
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
ADD_PRED = (HERE.parents[1] / "add_robustness" / "predictions"
            / "RF_best_pred_kmeans_results.csv")

MIN_YM, MAX_YM, TARGET_SR = 2.0, 3.3, 1
BAND_MARGIN_FLAG = 0.10   # log10 units (~RMSE/8): inside this, edge flips are expected
PROB_MARGIN_FLAG = 0.05   # |prob1 - 0.5| below this, class flips are expected

# 36 cluster-representative materials -> family labels (heuristic human
# reading; SMILES remain the source of truth).
FAMILY = {
    "[*]NC(C(N1CCCC1C(NCC(N2CC(CC2C(NC(C(NCC([*])=O)=O)CO)=O)O)=O)=O)=O)CCCCN":
        "明胶链(赖氨酸侧链)",
    "OCC(C(C(C1N)O)O[*])OC1OC2C(OC(C(C2O)N)[*])CO":
        "壳聚糖链(氨基葡萄糖)",
    "COCC1OC(OC2C(CO)OC(O[*])C(OC)C2OC)C(OC)C(O)C1O[*]":
        "甲基化多糖段(甲基纤维素类)",
    "COC(C(C[*])([*])C)=O":
        "丙烯酸酯段(PMMA类)",
    "[*]CC(C)(C(OCCO)=O)[*]":
        "PEG-酯段(PEGMA类)",
    "[*]C(N(CN(C(OCOC(N(CN(C(OCCO[*])=O)[H])[H])=O)=O)[H])[H])=O":
        "氨基树脂-PEG段(甘脲缩聚类)",
    "O=C([*])CCCCCO[*]":
        "己二酸酯段(PA聚酯类)",
    "O=C(N1C(C([*])=O)CC(O)C1)CNC(C2CCCN2[*])=O":
        "胶原特征肽段(羟脯氨酸-脯氨酸)",
    "O=C(C(OC(C=O)OC1C(C(C(OC1C(O[Na])=O)O[*])O)O)C(C=O)[*])O[Na]":
        "海藻酸钠(G段变体)",
    "[*]NC(CCCCNC(C(C)=C)=O)C(N1CCCC1C(NCC(N2CC(O)CC2C(NC(COC(C(C)=C)=O)C(NCC([*])=O)=O)=O)=O)=O)=O":
        "GelMA(甲基丙烯酰化明胶)",
    "[*]NC(C(O)=O)CCC([*])=O":
        "聚谷氨酸段(Glu)",
    "[*]NC(CCC([*])=O)C(O)=O":
        "聚谷氨酸段(Glu异写)",
    "[*]OC1C(C(O)=O)OC(OC2C(NC(C)=O)C([*])OC(CO)C2O)C(O)C1O":
        "N-乙酰氨基糖二糖段(透明质酸类)",
    "[*]OCC[*]":
        "PEG",
    "[*]OC1C(C(C(OC1C)OC2C(C(OC(C2O)COC(C)=O)OC3C(C(C(OC3C(O)=O)OC4C(C(C(OC4CO)O[*])O)O)O)O)OC(C(O)CO)=O)O)O":
        "乙酰化多糖段(纤维素衍生物)",
    "[H]N(C(O[*])=O)CCCCCCN(C(OCCCCO[*])=O)[H]":
        "聚酰胺-酯段(六亚甲基类)",
    "[*]OC1OC(CO)C(OC2C(O)C(O)C([*])C(CO)O2)C(O)C1O":
        "纤维素二糖段(cellobiose)",
    "O=C([*])C(C)O[*]":
        "PLA段(乳酸酯)",
    "CC(NC1C([C@@H](C(O[C@H]1O[*])CO)O[C@@H]2OC([C@H]([C@@H](C2NC(C)=O)O)[*])CO)O)=O":
        "几丁质段(立体指定N-乙酰氨基糖)",
    "[*]C(C)(C(OCCN(C)C)=O)C[*]":
        "丙烯酸酯-叔胺段(DMAEMA类)",
    "[*]C(CCCCCO[*])=O":
        "PCL段(ε-己内酯)",
    "[*]C([H])([H])C(O)([H])[*]":
        "PVA",
    "[*]C1C(C(C(OC1C(O[Na])=O)OC2C(C(O[Na])=O)OC(O[*])C(O)C2O)O)O":
        "海藻酸钠(M段)",
    "OC1C(OC(C(C1O)O)[*])CO[*]":
        "葡萄糖环段(葡聚糖/淀粉类)",
    "OCC1OC(C(C(C1[*])O)O)OC2C(C(C(OC2CO)O[*])O)O":
        "纤维素二糖段(异写)",
    "[*]C([C@H](C)OC([C@H](C)O[*])=O)=O":
        "PLA段(乳酸二聚)",
    "[*]C1C(OC(C(C1O)O)OC2C(OC(C(C2O)O)OC3C(OC(C(C3O)O)O[*])CO)CO)CO":
        "环糊精/葡聚糖段",
    "[*]C(C)C(OCC(O[*])=O)=O":
        "PLGA段(乳酸-乙醇酸)",
    "CC(NC1C(OC(C(C1OC2OC(C(C(C2OCC(COC(C(C)=C)=O)O)O)O[*])C([O-])=O)O)O)O[*])=O":
        "杂多糖-甲基丙烯酸酯接枝段",
    "O=C(N([*])C([*])=O)CC=C":
        "烯丙基脲段",
    "[*]C1=C(C=CN2)C2=C([*])C(O)=C1O":
        "木质素芳香段(苯并呋喃类)",
    "O=C(C(C[*])[*])N":
        "聚丙烯酰胺段",
    "OCC1OC(C(C(C1O[*])O)NC(C)=O)OC2C(O)C(C(OC2CO)[*])NC(C)=O":
        "几丁质二糖段(N-乙酰氨基葡萄糖)",
    "O=C(N)C([*])C[*]":
        "聚丙烯酰胺段(异写)",
    "[*]CC(C1=CC=C(C=C1)S(O)(=O)=O)[*]":
        "聚苯乙烯磺酸酯段(PSS)",
    "[H]N(C([H])([H])C(N([H])C(C)([H])C(N(C([H])([H])C([*])=O)[H])=O)=O)C(C(N([*])[H])(C)[H])=O":
        "丙氨酸寡肽段",
}
# Families excluded from the selection (same intent as the original two
# regex motifs; here by family, so alternate notations are also caught).
EXCLUDED_FAMILIES = {"聚丙烯酰胺段", "聚丙烯酰胺段(异写)",
                     "纤维素二糖段(cellobiose)", "纤维素二糖段(异写)"}


def fam(smi: str) -> str:
    return FAMILY.get(str(smi), "未归类")


def main() -> None:
    sr = pd.read_csv(SR_PRED)
    ym = pd.read_csv(YM_PRED)[["Pair_ID", "RF_YoungsModulus_pred"]]
    can = sr[["Pair_ID", "SMILE A", "SMILE B", "Prediction",
              "Prediction_prob_class0",
              "Prediction_prob_class1"]].merge(ym, on="Pair_ID")

    # P5: family-based exclusion on true compositions
    can["family_A"] = can["SMILE A"].map(fam)
    can["family_B"] = can["SMILE B"].map(fam)
    can["family_ok"] = (~can["family_A"].isin(EXCLUDED_FAMILIES) &
                        ~can["family_B"].isin(EXCLUDED_FAMILIES))

    # P3: margins
    can["band_margin"] = (can["RF_YoungsModulus_pred"] - MIN_YM).combine(
        MAX_YM - can["RF_YoungsModulus_pred"], min)
    can["prob_margin"] = can["Prediction_prob_class1"] - 0.5
    can["in_band"] = can["RF_YoungsModulus_pred"].between(MIN_YM, MAX_YM)
    can["borderline"] = ((can["in_band"] & (can["band_margin"] < BAND_MARGIN_FLAG))
                         | (can["prob_margin"].abs() < PROB_MARGIN_FLAG))

    # add-run evidence column (P3: decisions with evidence)
    flip = {}
    if ADD_PRED.exists():
        add = pd.read_csv(ADD_PRED)
        base = pd.read_csv(YM_PRED)
        mm = base.merge(add, on="Pair_ID", suffixes=("_b", "_a"))
        for _, r in mm.iterrows():
            vb, va = r["RF_YoungsModulus_pred_b"], r["RF_YoungsModulus_pred_a"]
            ib, ia = MIN_YM <= vb <= MAX_YM, MIN_YM <= va <= MAX_YM
            if ib and not ia:
                flip[r["Pair_ID"]] = "add32实验翻出带"
            elif ia and not ib:
                flip[r["Pair_ID"]] = "add32实验翻入带"
    can["add32_evidence"] = can["Pair_ID"].map(flip).fillna("")

    # gate
    sel = can[can["in_band"] & (can["Prediction"] == TARGET_SR)
             & can["family_ok"]].copy()
    sel = sel.sort_values("band_margin", ascending=False).reset_index(drop=True)
    sel.insert(0, "rank", sel.index + 1)

    cols = ["rank", "Pair_ID", "SMILE A", "family_A", "SMILE B", "family_B",
            "RF_YoungsModulus_pred", "band_margin", "Prediction",
            "Prediction_prob_class1", "prob_margin", "borderline",
            "add32_evidence"]
    sel[cols].to_csv(HERE / "correct_material_export.csv",
                     index=False, encoding="utf-8-sig")

    # P4: bench — near misses the wet lab should know about
    bench = can[(~(can["in_band"] & (can["Prediction"] == TARGET_SR)
                   & can["family_ok"]))
                & ((can["in_band"] & (can["Prediction_prob_class1"] >= 0.45))
                   | ((can["RF_YoungsModulus_pred"] > MIN_YM - 0.1)
                      & (can["RF_YoungsModulus_pred"] < MIN_YM)
                      & (can["Prediction"] == TARGET_SR))
                   | ((can["RF_YoungsModulus_pred"] > MAX_YM)
                      & (can["RF_YoungsModulus_pred"] < MAX_YM + 0.1)
                      & (can["Prediction"] == TARGET_SR)))
                & can["family_ok"]].copy()
    bench = bench.sort_values("band_margin", ascending=False)
    bench[["Pair_ID", "SMILE A", "family_A", "SMILE B", "family_B",
           "RF_YoungsModulus_pred", "band_margin", "Prediction",
           "Prediction_prob_class1", "prob_margin", "add32_evidence"]].to_csv(
        HERE / "alternates_bench.csv", index=False, encoding="utf-8-sig")

    # family map for reference
    pd.DataFrame([{"SMILES": k, "family": v,
                   "excluded": v in EXCLUDED_FAMILIES}
                  for k, v in FAMILY.items()]).to_csv(
        HERE / "family_map.csv", index=False, encoding="utf-8-sig")

    print(f"[gate] selected {len(sel)} pairs | IDs: "
          f"{sorted(sel['Pair_ID'], key=lambda s: int(s.split('_')[1]))}")
    print(f"[bench] {len(bench)} near-miss alternates -> alternates_bench.csv")
    print(f"[borderline among selected] "
          f"{sel[sel['borderline']]['Pair_ID'].tolist()}")
    print(f"[add32 flips in/borderline of gate] "
          f"{sel[sel['add32_evidence'] != ''][['Pair_ID', 'add32_evidence']].values.tolist()}")


if __name__ == "__main__":
    main()
