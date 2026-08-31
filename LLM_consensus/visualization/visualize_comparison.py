"""
Overall comparison visualization - Radar chart comparing all models
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional
from pathlib import Path

from .visualize_utils import MODEL_COLORS, MODEL_NAMES, get_output_dir


def plot_overall_comparison(
    data: Dict,
    base_dir: str = ".",
    save: bool = True,
    show: bool = False
) -> Optional[Path]:
    """
    Plot overall comparison - Radar chart comparing all models across metrics

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
    metrics = ['Avg CV', 'Avg ICC', 'Decision Consistency']

    model_scores = {}
    for model in models:
        # Calculate average CV
        avg_cv = np.mean([s['overall_cv']
                         for s in data[model]['scoring_reliability'].values()])

        # Calculate average ICC
        avg_icc = np.mean(list(data[model]['icc_scores'].values()))

        # Decision consistency
        winner_cons = data[model]['winner_consistency']['consistency_rate']

        model_scores[model] = {
            'Avg CV': 100 - avg_cv,  # Lower CV is better, convert to score
            'Avg ICC': avg_icc * 100,  # Convert ICC to percentage
            'Decision Consistency': winner_cons
        }

    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

    # Calculate angles
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    # Plot each model
    for model in models:
        values = [model_scores[model][metric] for metric in metrics]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2,
               label=MODEL_NAMES[model], color=MODEL_COLORS[model])
        ax.fill(angles, values, alpha=0.15, color=MODEL_COLORS[model])

    # Set labels and grid
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=12)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Title and legend
    plt.title('Comprehensive LLM Model Reliability Comparison\n(Higher values indicate better reliability)',
             fontsize=14, fontweight='bold', pad=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

    plt.tight_layout()

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / 'overall_comparison_radar.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Saved: overall_comparison_radar.png")

    if show:
        plt.show()

    plt.close()
    return output_path
