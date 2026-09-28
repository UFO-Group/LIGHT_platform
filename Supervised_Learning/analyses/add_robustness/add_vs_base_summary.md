# add 数据稳健性 —— 阶段 A(base vs base+32)概要

- 参数漂移:base {'n_estimators': 400, 'max_depth': 20, 'min_samples_split': 16, 'min_samples_leaf': 2, 'max_features': 0.2}
  add  {'n_estimators': 600, 'max_depth': 25, 'min_samples_split': 16, 'min_samples_leaf': 2, 'max_features': 0.2}
  identical = False
- 诚实指标(GroupKFold(10) per-fold 均值±std):
  base(1629 行): R2 = 0.5078 ± 0.0565, RMSE = 0.801, MAE = 0.6284
  add (1661 行): R2 = 0.4889 ± 0.1073, RMSE = 0.8638, MAE = 0.6542
- 候选预测(630 对,base 模型 vs add 模型):Spearman = 0.9879, max|Δpred| = 1.3792
- 终选自检(deploy_report 原文):
  final selection: 10 pairs | kept 9/10 | dropped ['Pair_124'] | added ['Pair_7']
  [WARNING] final selection DIFFERS from the expected list. If training data or candidates changed this may be legitimate — re-verify before any deployment claim.
- 背景(旧泄漏协议 add 运行,口径不可比):R2 = 0.4948 ± 0.0803