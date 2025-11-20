### All unsupervised learning scripts are run in the unsupervised environment.

### In the unsupervised_learning folder:

- 1.Used for merging the two databases of Young's modulus and swelling ratio.
```bash
python data-process.py
```

- 2.Generate 1024-length fingerprints from the merged database.
```bash
python morgan.py
```

- 3.Perform unsupervised clustering.
```bash
python unsupervised.py
```

- 4.Analyze the unsupervised results.
```bash
python analyze_unsupervised.py
```

- Additionally, running the command below directly reproduces the unsupervised classification results in the paper:
```bash
python umap2d-kmeans.py
```

### In the candidate_umap folder:

- 1.Count all SMILES appearing in the database and form all pairwise combinations (all_AB_SMILES), and generate Morgan fingerprints (compressed into all_random_smiles_AB_concat1024.rar)
```bash
python all_AB_smiles2morgan.py
```

- 2.SMILES pairs that may form target properties appear in certain clusters. These pairs are predicted by the supervised model (Prediction-1028-ALL2.csv), and then filtered to obtain candidate components (Prediction-1028-ALL2-candidate.csv). Morgan fingerprints are generated for both files.
```bash
python cluster-3-AB-morgan.py
```

- 3.Used to generate the UMAP distribution plot for candidate components
```bash
python umap-candidate.py
```
