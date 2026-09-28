# add_robustness — Pipeline robustness under +32 rows of literature data (analysis; not part of the runtime pipeline)

Date: 2026-09-27. Data source: `DataBase/youngs_modulus_add.csv` (base 1629
+ 32 newly extracted literature rows, a strict superset; the 630-candidate
library is unchanged — replicating the original `_add` manual-rerun
semantics, but under the honest protocol).

## Protocol

Identical to the production pipeline, reusing the production modules via
subprocess: morgan_pooling (alpha 3 / radius 3 / 1024) -> GroupKFold(5) x
96-combo grid selection -> deploy_rf (GroupKFold(10) honest evaluation +
full-data retrain + candidate prediction + final-selection self-check).

## Results (add_vs_base_summary.md)

- Parameter drift {400, d20} -> {600, d25}; paired test mean diff +0.0010,
  **Wilcoxon p = 0.557** (re-selection gives no significant gain; the
  change is data-driven)
- Honest R2 0.508±0.057 -> 0.489±0.107; candidate-prediction Spearman 0.988
- **Final selection 9/10**: Pair_124 falls below the lower band edge by
  0.012; Pair_7 crosses the upper edge by 0.001 (a direct measurement of
  the documented band-edge fragility; Pair_229 stays in by only 0.015)

## Files

- `01_add_pipeline.py` — full pipeline orchestration (pooling -> selection
  -> deployment -> summary)
- `02_paired_drift.py` — paired same-fold comparison of frozen base params
  vs add-reselected params
- `add_vs_base_summary.{md,json}`, `paired_drift.json`, `rf_grid/`,
  `rf_cv10/{cv10_metrics.csv,deploy_report.txt}`, `predictions/`,
  `features/` (selection/deployment intermediate artifacts)
- **Not included**: `rf_cv10/fold_models/*.joblib` (deployed-model
  binaries, regenerable, deliberately kept out of the repo)

## Running

```bash
cd Supervised_Learning/analyses/add_robustness
C:/Users/Administrator/anaconda3/envs/supervised/python.exe 01_add_pipeline.py
C:/Users/Administrator/anaconda3/envs/supervised/python.exe 02_paired_drift.py
```

Timing and skip semantics: the pooling/selection steps are skipped when
their artifacts already exist (cold selection run ~9 min); **the
deployment step always re-runs because the model joblib is not kept in
the repo** (~4 min, deterministic — values reproduce the committed
cv10_metrics/deploy_report exactly and rewrite them). 02 takes ~2-3 min
(20 RF fits) and rewrites paired_drift.json.

## Migration note

Promoted on 2026-09-28 from the repo-root sandbox `add_robustness/`
(path constants adapted); the original sandbox is kept.
