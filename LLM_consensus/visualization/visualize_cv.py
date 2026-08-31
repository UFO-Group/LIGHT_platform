"""
CV (Coefficient of Variation) visualization - Bar chart comparing CV across models and criteria
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Optional
from pathlib import Path

from .visualize_utils import MODEL_COLORS, MODEL_NAMES, CRITERION_NAMES, get_output_dir


def plot_cv_comparison(
    data: Dict,
    base_dir: str = ".",
    save: bool = True,
    show: bool = False
) -> Optional[Path]:
    """
    Plot CV comparison bar chart across models and criteria

    Parameters
    ----------
    data : Dict
        Analysis results data
    base_dir : str
        Base directory path (default: current directory)
    save : bool
        Whether to save the figure (default: True)
    show : bool
        Whether to display the figure (default: False)

    Returns
    -------
    Optional[Path]
        Path to saved file if save=True, None otherwise
    """
    # Prepare data
    models = list(data.keys())
    criteria = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
               'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']

    cv_data = []
    for model in models:
        for criterion in criteria:
            if criterion in data[model]['scoring_reliability']:
                cv_data.append({
                    'Model': model,
                    'Criterion': CRITERION_NAMES[criterion],
                    'CV': data[model]['scoring_reliability'][criterion]['overall_cv']
                })

    df = pd.DataFrame(cv_data)

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(14, 6))

    models_list = list(df['Model'].unique())
    x = np.arange(len(criteria))
    width = 0.2

    for i, model in enumerate(models_list):
        model_data = df[df['Model'] == model]['CV'].values
        ax.bar(x + i * width, model_data, width,
               label=MODEL_NAMES[model], color=MODEL_COLORS[model], alpha=0.8)

    # Add reference lines
    ax.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='Excellent (CV<10%)')
    ax.axhline(y=20, color='orange', linestyle='--', alpha=0.5, label='Fair (CV≥20%)')

    ax.set_xlabel('Scoring Criteria', fontsize=12, fontweight='bold')
    ax.set_ylabel('Coefficient of Variation CV (%)', fontsize=12, fontweight='bold')
    ax.set_title('CV Comparison Across Scoring Criteria\n(Lower is better)',
                fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(CRITERION_NAMES.values(), rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / 'cv_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Saved: cv_comparison.png")

    if show:
        plt.show()

    plt.close()
    return output_path
