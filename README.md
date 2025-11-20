# LIGHT: Automated discovery of optimal hydrogel components by the intelligent agent

## Features

### 1. Database Construction Module (Automated Data Extraction)

- This project builds a high-throughput literature data extraction system using the DeepSeek-32B model and PDF/HTML parsing tools (such as pdfplumber).

- All extracted results are stored in standardized JSON format, ensuring semantic consistency, traceability, and convenience for downstream modeling and processing.

### 2. Agent-Driven Automated Modeling and High-Throughput Screening

- The intelligent agent completes the following tasks without manual intervention:

Parse the hydrogel database and determine the number of samples available for unsupervised learning.

Run the unsupervised learning module to analyze clustering patterns and the structural–property distribution of hydrogel components.

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

Use the DeepSeek API to extract information from literature. See README inside Automated_Data_Extraction for details.

### Unsupervised_Learning

Use automatically extracted data to perform unsupervised learning and determine combinations. See README in Unsupervised_Learning for details.

### Supervised_Learning

Use automatically extracted data to train regression and classification models to predict Young’s modulus and swelling ratio. See README in Supervised_Learning for details.

## File Structure

Automated_Data_Extraction/ — Automated data extraction folder
Automated_Data_Extraction/Split_pdf.ipynb — PDF splitting
Automated_Data_Extraction/Data_Extraction/ — Literature extraction scripts
Automated_Data_Extraction/Table_Generation.ipynb — Convert extracted information into tables
Automated_Data_Extraction/Standardize_Units.ipynb — Standardize units in tables

Unsupervised_Learning/ — Unsupervised learning folder
Unsupervised_Learning/candidate_umap/ — Candidate component distribution plots
Unsupervised_Learning/database — Original database and data distribution scripts
Unsupervised_Learning/unsupervised_learning — Scripts for unsupervised clustering

Supervised_Learning/ — Supervised learning folder
Supervised_Learning/Regression_Model — Regression model scripts
Supervised_Learning/Classification_Model — Classification model scripts
Supervised_Learning/High-throughput predict — Unsupervised results and prediction scripts
Supervised_Learning/DataBase — Original database and data distribution scripts

## About
Developed by:
UFO Group,
China, Donghua University.

## License
This project is licensed under the MIT License.

