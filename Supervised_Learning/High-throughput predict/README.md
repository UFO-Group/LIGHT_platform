### How to create Morgan fingerprint.
```bash
python morgan_pooling.py \
  --in_csv Path/kmeans_results.csv \
  --polymer_cols "SMILE A" "SMILE B" \
  --alpha 3 --radius 3 --nbits 1024 \
  --out_csv Path/kmeans-pooled.csv
```

### How to predict Regerssion.
- You need to identify the best model and rename the file using R², RMSE, and MAE. e.g. fold_08_best_model.joblib to best_model.joblib.
```bash
python predict.py \
  --in_csv Path/kmeans-pooled.csv \
  --source_csv Path/kmeans_results.csv \
  --out_csv Path/Result-youngs.csv \
  --model_dir Path/rf_cv10/fold_models/ 
```

### How to predict Classification.
- You need to identify the best model and rename the file using Acc、Acc_class_0、Acc_class_1. e.g. fold_06_model.joblibb to best_model.joblib.
```bash
python predict.py \
  --in_csv Path/kmeans-pooled.csv \
  --source_csv Path/kmeans_results.csv \
  --out_csv Path/Result-swelling.csv \
  --model_dir Path/rf_cls_cv10_t9/cv10/ 
```
