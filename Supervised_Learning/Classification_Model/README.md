### How to create Morgan fingerprint.
```bash
python morgan_pooling.py \
  --in_csv swelling_ratio.csv \
  --polymer_cols "SMILE A" "SMILE B" "SMILE C" \
  --alpha 3 --radius 3 --nbits 1024 \
  --out_csv Path/SMILES-pooled-morgan.csv
```

### How to run Classification_model.
```bash
python pipeline.py \
  --in_csv  Path/SMILES-pooled-morgan.csv \
  --src_col "Swelling Ratio (times)" \
  --threshold 9 \
  --use_cv10 1
```

### How to predict
- You need to identify the best model and rename the file using Acc、Acc_class_0、Acc_class_1. e.g. fold_06_model.joblibb to best_model.joblib.
```bash
python predict.py \
  --in_csv Path/kmeans-pooled.csv \
  --source_csv Path/kmeans_results.csv \
  --out_csv Path/Result-swelling.csv \
  --model_dir Path/rf_cls_cv10_t9/cv10/ 
```

###  How to draw Classification_Matrix.
```bash
python draw_Matrix.py \
  --csv_train   Path/rf_cls_cv10_t9/cv10/fold_06_train.csv \
  --csv_test    Path/rf_cls_cv10_t9/cv10/fold_06_valid.csv \
  --y_col       y_true \
  --yhat_col    y_pred \
  --out_train   Path/CM/confmat_train.png \
  --out_test    Path/CM/confmat_valid.png \
  --out_dir     Path/CM/
  --cmap        Blues \
  --rotate_xticks 0 \
  --normalize   none
```
###  How to draw Classification_ROC.
```bash
python draw_ROC.py \
  --csv_train Path/rf_cls_cv10_t9/cv10//fold_06_train.csv \
  --csv_test  Path/rf_cls_cv10_t9/cv10/fold_06_valid.csv \
  --out_dir   Path/ROC \
  --train_color 109,109,255 \
  --test_color  "#F3A5D9" \
  --fill
```

