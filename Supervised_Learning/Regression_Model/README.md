# Supervised Regression Model Workflow (group-aware honest pipeline)

This folder provides the supervised-learning workflow for Young's-modulus
regression. Polymer/formulation SMILES are converted into pooled
Morgan-fingerprint features; a random-forest regressor is selected by
**group-aware cross-validation** (identical materials never straddle
folds), evaluated honestly, retrained on the full training set for
deployment, and used to predict the 630-candidate library. A built-in
self-check replays the final-selection rule and reports any change.

The pre-migration stages (single-holdout RF grid, plain-KFold MLP/SVM
grids, best-fold model manufacturing, standalone predict script) were
removed from HEAD and remain in git history only.

## 1. Pipeline

```text
run_pipeline.py                          # one-click entry point
│
└── regression_main.py                   # 4-step controller
    ├── STEP 1  main_regression/morgan_pooling.py
    │           radius 3 / alpha 3 / 1024 bits (pinned)
    ├── STEP 2  main_regression/select_params_groupcv.py
    │           96-combo production grid scored by GroupKFold(5) on
    │           _fp_hash (MD5 of the fingerprint row); deterministic,
    │           tie rule = first combo in enumeration order
    ├── STEP 3  main_regression/deploy_rf.py
    │           a) honest evaluation: GroupKFold(10) on _fp_hash
    │              -> cv10_metrics.csv (per-fold R2/RMSE/MAE)
    │           b) manufacturing: full-data retrain with the selected
    │              params -> fold_models/best_model.joblib
    │           c) candidate prediction (schema consumed by the
    │              selection stage) + final-selection self-check
    │              replicating Agent/Selection_pipeline.py (report-only)
    └── STEP 4  model_candidates_for_llm.json (single RF entry)
                -> API/advise_best_model_with_api.py
                -> draw_pipline.py (scatter for the best fold)
```

Headline numbers (production run, GroupKFold(10) per-fold mean):
**R2 = 0.508 ± 0.057, RMSE = 0.801, MAE = 0.628** (log10 kPa);
the final selection is reproduced exactly (10/10).

Caveat: hyperparameters were selected on the same dataset (one-shot
group selection), so the honest-fold scores are mildly optimistic.
Robustness checks (added data, frozen-vs-reselected params) live in
`../analyses/add_robustness/`.

## 2. Folder structure (current)

```text
Regression_Model/
├── run_pipeline.py            # one-click: regression -> advisory -> draw
├── regression_main.py         # 4-step controller (see above)
├── draw_pipline.py            # scatter plots for the best R2 fold
├── README.md
│
├── main_regression/
│   ├── morgan_pooling.py          # SMILES -> pooled Morgan features
│   ├── select_params_groupcv.py   # group-aware RF hyperparameter selection
│   └── deploy_rf.py               # honest eval + full retrain + predict
│                                  #   + final-selection self-check
│
├── API/
│   ├── advise_best_model_with_api.py
│   └── API.py
│
├── draw/
│   └── draw_r2.py                 # parity-plot style used by the figures
│
└── results/YoungsModulus/
    ├── features/                  # pooled feature CSV
    ├── rf_grid/                   # best_params.json + selection_landscape.csv
    ├── rf_cv10/                   # cv10_metrics.csv, deploy_report.txt,
    │   └── fold_models/           #   full-data-retrain best_model.joblib
    ├── predictions/               # candidate prediction CSV
    ├── draw/                      # generated figures
    └── model_candidates_for_llm.json
```

Legacy outputs of the retired protocol are kept for the record and are
**not** produced by the current pipeline: `Best_result/`, `mlp_grid/`,
`svm_grid/`, `ols_linear/`, `runs/`, `results/YoungsModulus_add/`.

Post-hoc analyses (add-data robustness, four-model comparison evidence,
candidate-annotation audit, corrected material export) live in
`../analyses/` — see the README in each analysis folder.

## 3. Data flow and file formats

1. The original SMILES/formulation CSV (`../DataBase/youngs_modulus.csv`,
   columns `SMILE A/B/C`, `Young's Modulus (kPa) log10`, `Source`) is
   converted into a 1024-dim pooled Morgan-fingerprint CSV
   (`fp_0` ... `fp_1023` + target column).
2. The feature CSV drives selection, honest evaluation and the
   full-data retrain.
3. The deployed model predicts the 630-candidate library
   (`../High-throughput predict/kmeans-pooled.csv`), producing:

| Pair_ID | SMILE A | SMILE B | row_index | RF_YoungsModulus_pred |
|---|---|---|---:|---:|
| Pair_1 | `[*]NC(...)` | `[*]NC(...)` | 0 | 2.920 |
| ... | ... | ... | ... | ... |

Note (see `../analyses/pair_id_rejoin_audit/`): the composition
annotation of the 630 feature rows is authoritative in
`../Classification_Model/results/SwellingRatio/SwellingRatio_predict.csv`
(fingerprint-verified 630/630); the SMILES columns of
`kmeans_results.csv` are misaligned with the feature rows and are used
only as a row-count/ID source by the pipeline.

## 4. Running examples

```bash
# one-click (recommended)
python run_pipeline.py

# step by step
python main_regression/morgan_pooling.py \
  --in_csv ../DataBase/youngs_modulus.csv \
  --polymer_cols "SMILE A" "SMILE B" "SMILE C" \
  --target_col "Young's Modulus (kPa) log10" \
  --alpha 3 --radius 3 --nbits 1024 \
  --out_csv results/YoungsModulus/features/youngs_modulus-pooled-morgan.csv

python main_regression/select_params_groupcv.py \
  --in_csv results/YoungsModulus/features/youngs_modulus-pooled-morgan.csv \
  --target "Young's Modulus (kPa) log10" \
  --save_dir results/YoungsModulus/rf_grid --n_splits 5 --seed 42

python main_regression/deploy_rf.py \
  --in_csv results/YoungsModulus/features/youngs_modulus-pooled-morgan.csv \
  --target "Young's Modulus (kPa) log10" \
  --params_json results/YoungsModulus/rf_grid/best_params.json \
  --save_dir results/YoungsModulus/rf_cv10 --honest_folds 10 --seed 42 \
  --predict_in_csv "../High-throughput predict/kmeans-pooled.csv" \
  --predict_source_csv "../High-throughput predict/kmeans_results.csv" \
  --pred_out_csv results/YoungsModulus/predictions/RF_best_pred_kmeans_results.csv \
  --sr_pred_csv ../Classification_Model/results/SwellingRatio/SwellingRatio_predict.csv
```

`run_pipeline.py` chains these with the advisory and plotting steps;
`regression_main.py` is the 4-step controller behind it.

Python: 3.9+ (conda env `supervised`).
