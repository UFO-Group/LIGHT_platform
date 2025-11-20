### How to create Morgan fingerprint
```bash
python morgan_pooling.py \
  --in_csv youngs_modulus.csv \
  --polymer_cols "SMILE A" "SMILE B" "SMILE C" \
  --alpha 3 --radius 3 --nbits 1024 \
  --out_csv Path/SMILES-pooled-morgan.csv
```

### How to run RF_Regression
```bash
python baseline_RF.py \
  --in_csv Path/SMILES-pooled-morgan.csv \
  --target "Young's Modulus (kPa) log10" \
  --model rf \
  --seed 42 \
  --save_dir Path/rf_cv10 \
  --cv10 \
  --cv_folds 10 \
  --save_train_pred \
  --rf_n_estimators 400 --rf_max_depth 15 --rf_max_features 0.2 \
  --rf_min_samples_leaf 2 --rf_min_samples_split 12
```

### How to run mlp and svm model
```bash
python train_mlp_svm_pipeline.py \
  --in_csv  Path/SMILES-pooled-morgan.csv \
  --target  "Young's Modulus (kPa) log10" \
  --out_root Path/runs \
  --cv10 1 \
  --cv_folds 10
```
  
### How to run OLS_linear_regression
```bash
python baseline_OLS_linear_regression.py
```

### How to predict 
- You need to identify the best model and rename the file using R², RMSE, and MAE. e.g. fold_08_best_model.joblib to best_model.joblib
```bash
python predict.py \
  --in_csv Path/kmeans-pooled.csv \
  --source_csv Path/kmeans_results.csv \
  --out_csv Path/Result-youngs.csv \
  --model_dir Path/rf_cv10/fold_models/ 
```

### How to run a grid search for RF
```bash
python rf_grid_loop.py \
  --in_csv Path/SMILES-pooled-morgan.csv \
  --target "Young's Modulus (kPa) log10" \
  --save_dir Path/rf_grid_loop \
  --id_cols SampleID,RecipeID \
  --test_size 0.2
```

### How to run a grid search for MLP
```bash
python grid_mlp.py \
  --in_csv Path/SMILES-pooled-morgan.csv \
  --target "Young's Modulus (kPa) log10" \
  --save_dir Path/mlp_grid
```

### How to run a grid search for SVM
```bash
python grid_svm.py \
  --in_csv Path/SMILES-pooled-morgan.csv \
  --target "Young's Modulus (kPa) log10" \
  --save_dir Path/svm_grid
```

### How to draw RF R2-curve
```bash
python draw_r2.py \
  --train_csv Path/rf_cv10/fold_08_train.csv \
  --test_csv Path/rf_cv10/fold_08_valid.csv \
  --outdir Path/rf_cv10/draw
```

### How to draw MLP R2-curve
```bash
python draw_r2.py \
  --train_csv Path/runs/mlp/fold_08_train.csv \
  --test_csv Path/runs/mlp/fold_08_valid.csv \
  --outdir Path/runs/mlp/draw
```

### How to draw SVM R2-curve
```bash
python draw_r2.py \
  --train_csv Path/runs/svm/fold_05_train.csv \
  --test_csv Path/runs/svm/fold_05_valid.csv \
  --outdir Path/runs/svm/draw
```

### How to draw OLS R2-curve
```bash
python draw_r2.py \
  --train_csv Path/runs/linear_ols/fold_8/fold_8_train.csv \
  --test_csv Path/runs/linear_ols/fold_8/fold_8_valid.csv \
  --outdir Path/runs/linear_ols/fold_8/draw
```


