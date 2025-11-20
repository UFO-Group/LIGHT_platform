# LIGHT: Automated discovery of optimal hydrogel components by the intelligent agent.

## Features

### 1. Database Construction Module (Automated Data Extraction)

- This project builds a high-throughput literature data extraction system using the DeepSeek-32B model and PDF/HTML parsing tools (such as pdfplumber).

- All extracted results are stored in standardized JSON format, ensuring semantic consistency, traceability, and convenience for downstream modeling and processing.

### 2. Agent-Driven Automated Modeling and High-Throughput Screening

The intelligent agent completes the following tasks without manual intervention:

* Parse the hydrogel database and determine the number of samples available for unsupervised learning.

* Run the unsupervised learning module to analyze clustering patterns and the structural–property distribution of hydrogel components.

### 3. Unsupervised Learning Module

- This module explores the distribution and clustering patterns of hydrogels in the “structure–property space.”

### 4. Supervised Learning Module

- The supervised module establishes nonlinear mapping relationships between molecular structures and material properties.

- Using automatically extracted data, we train regression and classification models to predict Young’s modulus and swelling ratio, respectively.

## Installation

### 1. Clone this repository:

```bash
git clone https://github.com/UFO-Group/LIGHT_platform/
cd LIGHT_platform
```

### 2. Install dependencies
   (Different environments for different modules)

- For literature extraction:
```bash
cd Automated_Data_Extraction
pip install -r requirements.txt
```

- For Unsupervised Learning:
```bash
cd Unsupervised_Learning
pip install -r requirements.txt
```

- For Supervised Learning:
```bash
cd Supervised_Learning
pip install -r requirements.txt
```

### 3. Configure your API and URL in Automated_Data_Extraction
```python
def call_deepseek_llm(prompt):
   client = OpenAI(
      api_key="Your_API_KEY",
      base_url="Your_API_URL"
   )
```

## Usage

### Automated_Data_Extraction

- Use the DeepSeek API to extract information from literature. See README inside Automated_Data_Extraction for details.

### Unsupervised_Learning

- Use automatically extracted data to perform unsupervised learning and determine combinations. See README in Unsupervised_Learning for details.

### Supervised_Learning

- Use automatically extracted data to train regression and classification models to predict Young’s modulus and swelling ratio. See README in Supervised_Learning for details.

## File Structure

```text
LIGHT_platform
|   README.md
|   
+---Automated_Data_Extraction
|   |   README.md
|   |   requirements.txt
|   |   Split_pdf.ipynb
|   |   Standardize_Units.ipynb
|   |   Table_Generation.ipynb
|   |   
|   \---Data_Extraction
|           API-YoungsModulus.py
|           Clean.py
|           contains_keywords-swelling.py
|           contains_keywords-youngs.py
|           main-PDF-Swellingratio.ipynb
|           main-PDF-Youngsmodulus.ipynb
|           TextNormalizer.py
|           
+---Supervised_Learning
|   |   requirements.txt
|   |   
|   +---Classification_Model
|   |   |   draw_Matrix.py
|   |   |   draw_ROC.py
|   |   |   morgan_pooling.py
|   |   |   pipeline.py
|   |   |   predict.py
|   |   |   README.md
|   |   |   train_rf.py
|   |   |   
|   |   \---Best_result
|   |           best_model.joblib
|   |           cv10_metrics.csv
|   |           fold_06_train.csv
|   |           fold_06_valid.csv
|   |           
|   +---DataBase
|   |       Data_Distribution_Statistics_Plot.ipynb
|   |       swelling_ratio.csv
|   |       youngs_modulus.csv
|   |       
|   +---High-throughput predict
|   |       kmeans-pooled.csv
|   |       kmeans_results.csv
|   |       README.md
|   |       Result-swelling.csv
|   |       Result-youngs.csv
|   |       
|   \---Regression_Model
|       |   README.md
|       |   
|       +---Best_result
|       |   +---MLP
|       |   |       cv10_metrics.csv
|       |   |       fold_08_train.csv
|       |   |       fold_08_valid.csv
|       |   |       
|       |   +---OLS
|       |   |       fold_8_train.csv
|       |   |       fold_8_valid.csv
|       |   |       
|       |   +---RF
|       |   |       best_model.joblib
|       |   |       cv10_metrics.csv
|       |   |       fold_08_train.csv
|       |   |       fold_08_valid.csv
|       |   |       
|       |   \---SVM
|       |           cv10_metrics.csv
|       |           fold_05_train.csv
|       |           fold_05_valid.csv
|       |           
|       +---draw
|       |       draw_r2.py
|       |       
|       +---grid
|       |       grid_mlp.py
|       |       grid_svm.py
|       |       rf_grid_loop.py
|       |       
|       +---main_regression
|       |       baseline_mlp_svm.py
|       |       baseline_OLS_linear_regression.py
|       |       baseline_RF.py
|       |       morgan_pooling.py
|       |       train_mlp_svm_pipeline.py
|       |       
|       \---predict
|               predict.py
|               
\---Unsupervised_Learning
    |   morgan_pooling.py
    |   README.md
    |   requirements.txt
    |   
    +---candidate_umap
    |       all_AB_smiles2morgan.py
    |       all_random_smiles_AB_concat1024.rar
    |       candidate_umap_coordinates.csv
    |       cluster-3-AB-morgan.py
    |       Prediction-1028-ALL2-1024.npy
    |       Prediction-1028-ALL2-candidate-1024.npy
    |       Prediction-1028-ALL2-candidate-process.csv
    |       Prediction-1028-ALL2-candidate.csv
    |       Prediction-1028-ALL2-process.csv
    |       Prediction-1028-ALL2.csv
    |       smiles_count.csv
    |       smiles_count_random_2.csv
    |       umap-candidate.py
    |       umap_candidate_visualization.png
    |       Untitled.ipynb
    |       
    +---database
    |       swelling_ratio.csv
    |       youngs_modulus.csv
    |       
    \---unsupervised_learning
        |   AB_concat1024.npy
        |   analyze_unsupervised.py
        |   cluster_umap_kmeans.png
        |   cluster_umap_kmeans_from_npy.png
        |   data-process.py
        |   final_two_smiles_with_modulus.csv
        |   morgan.py
        |   umap2d-kmeans.py
        |   umap2d.npy
        |   unsupervised.py
        |   
        +---clusters
        |       cluster_0.csv
        |       cluster_1.csv
        |       cluster_2.csv
        |       cluster_3.csv
        |       cluster_4.csv
        |       cluster_5.csv
        |       cluster_statistics.csv
        |       
        \---clusters-from-umap
                cluster_0.csv
                cluster_1.csv
                cluster_2.csv
                cluster_3.csv
                cluster_4.csv
                cluster_5.csv
```

## About

Developed by:

UFO Group,

China, Donghua University.

## License

This project is licensed under the MIT License.





