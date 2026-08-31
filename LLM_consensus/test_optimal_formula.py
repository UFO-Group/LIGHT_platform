"""
Simple test for optimal formula calculation
"""

import json
import pandas as pd

# Read summary file
with open('analysis/popularity_bias_analysis/analysis_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Test GPT-5
gpt5 = data['summary']['gpt-5']

print('GPT-5 data:')
print(f\"Formula ID: {gpt5['optimal_formula']['formula_id']}\")
print(f\"Formula Name: {gpt5['optimal_formula']['formula_name']}\")
print(f\"Total Score: {gpt5['optimal_formula']['total_score']}")
print()

# Get dimension scores
dim_scores = gpt5['optimal_formula']['dimension_scores']
print()
print('Dimension scores:')
for dim, score in dim_scores.items():
    print(f'  {dim}: {score}')

# Test total calculation
dims = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization', 'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']
expected_total = sum(gpt5['optimal_formula']['dimension_scores'].values())

print()
print(f'\nExpected total: {expected_total}')
print(f'Actual total: {gpt5['optimal_formula']['total_score']}')
print()
print(f'Difference: {gpt5['optimal_formula']['total_score'] - expected_total}')
"
