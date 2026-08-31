"""
ICC (Intraclass Correlation Coefficient) visualization - Heatmap comparing ICC across models and criteria
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Optional
from pathlib import Path

from .visualize_utils import MODEL_NAMES, CRITERION_NAMES, get_output_dir


def plot_icc_comparison(
    data: Dict,
    base_dir: str = ".",
    save: bool = True,
    show: bool = False
) -> Optional[Path]:
    """
    Plot ICC comparison heatmap across models and criteria

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

    # Create ICC matrix
    icc_matrix = pd.DataFrame(index=criteria, columns=models)

    for model in models:
        for criterion in criteria:
            if criterion in data[model]['icc_scores']:
                icc_matrix.loc[criterion, model] = data[model]['icc_scores'][criterion]

    icc_matrix = icc_matrix.astype(float)

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))

    sns.heatmap(icc_matrix, annot=True, fmt='.4f', cmap='RdYlGn',
               vmin=0, vmax=1, cbar_kws={'label': 'ICC Value'},
               linewidths=0.5, linecolor='white', ax=ax)

    ax.set_title('Intraclass Correlation Coefficient (ICC) Heatmap\n(Higher values indicate better consistency)',
                fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax.set_ylabel('Scoring Criteria', fontsize=12, fontweight='bold')

    # Use English criterion names for y-axis
    ax.set_yticklabels([CRITERION_NAMES.get(c, c) for c in icc_matrix.index])
    ax.set_xticklabels([MODEL_NAMES.get(m, m) for m in icc_matrix.columns])

    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)

    plt.tight_layout()

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / 'icc_heatmap.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Saved: icc_heatmap.png")

    if show:
        plt.show()

    plt.close()
    return output_path
