"""
Model detail visualization - Multi-panel detailed analysis for a single model
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Optional
from pathlib import Path

from .visualize_utils import MODEL_COLORS, MODEL_NAMES, CRITERION_NAMES, get_output_dir


def plot_model_detail(
    data: Dict,
    model_name: str,
    base_dir: str = ".",
    save: bool = True,
    show: bool = False
) -> Optional[Path]:
    """
    Plot detailed analysis for a single model

    Parameters
    ----------
    data : Dict
        Analysis results data
    model_name : str
        Name of the model to visualize
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
    if model_name not in data:
        print(f"[ERROR] Model {model_name} does not exist")
        return None

    model_data = data[model_name]

    # Create subplots
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    # 1. CV radar chart
    ax1 = fig.add_subplot(gs[0, 0], polar=True)
    criteria = list(model_data['scoring_reliability'].keys())

    cv_values = [model_data['scoring_reliability'][c]['overall_cv'] for c in criteria]

    angles = np.linspace(0, 2 * np.pi, len(criteria), endpoint=False)
    cv_values = cv_values + [cv_values[0]]
    angles = np.concatenate([angles, [angles[0]]])

    ax1.plot(angles, cv_values, 'o-', linewidth=2, color=MODEL_COLORS[model_name])
    ax1.fill(angles, cv_values, alpha=0.25, color=MODEL_COLORS[model_name])
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels([CRITERION_NAMES.get(c, c).replace('_', ' ')
                         for c in criteria], fontsize=8)
    ax1.set_ylim(0, max(cv_values) * 1.1)
    ax1.set_title('Coefficient of Variation', fontweight='bold', fontsize=11)
    ax1.grid(True)

    # 2. ICC bar chart
    ax2 = fig.add_subplot(gs[0, 1])
    icc_criteria = list(model_data['icc_scores'].keys())
    icc_values = [model_data['icc_scores'][c] for c in icc_criteria]

    colors_icc = ['green' if v > 0.8 else 'orange' if v > 0.6 else 'red'
                  for v in icc_values]
    ax2.barh(range(len(icc_criteria)), icc_values, color=colors_icc,
            alpha=0.7, edgecolor='black')
    ax2.set_yticks(range(len(icc_criteria)))
    ax2.set_yticklabels([CRITERION_NAMES.get(c, c).replace('_', ' ')
                         for c in icc_criteria], fontsize=8)
    ax2.set_xlabel('ICC Value', fontsize=10)
    ax2.set_title('Intraclass Correlation Coefficient',
                 fontweight='bold', fontsize=11)
    ax2.set_xlim(0, 1)
    ax2.axvline(x=0.8, color='green', linestyle='--', alpha=0.5, label='Excellent')
    ax2.axvline(x=0.6, color='orange', linestyle='--', alpha=0.5, label='Good')
    ax2.legend(fontsize=8)
    ax2.grid(axis='x', alpha=0.3)

    # 3. Winner distribution pie chart
    ax3 = fig.add_subplot(gs[0, 2])
    wc = model_data['winner_consistency']
    if 'error' not in wc and 'winner_distribution' in wc:
        dist = wc['winner_distribution']
        formulas = sorted(dist.keys())
        sizes = [dist[f] for f in formulas]
        labels = [f'Formula {f}' for f in formulas]

        colors_pie = plt.cm.Set3(np.linspace(0, 1, len(formulas)))
        wedges, texts, autotexts = ax3.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors_pie, startangle=90)
        ax3.set_title(f'Winner Distribution\n(Consistency: {wc["consistency_rate"]:.1f}%)',
                     fontweight='bold', fontsize=11)

    # 4. CV range box plot
    ax4 = fig.add_subplot(gs[1, :])

    summary_data = []
    for criterion in criteria:
        stats = model_data['scoring_reliability'][criterion]
        summary_data.append({
            'Criterion': CRITERION_NAMES[criterion],
            'Mean': stats['overall_cv'],
            'Max': stats['max_cv'],
            'Min': stats['min_cv']
        })

    df_summary = pd.DataFrame(summary_data)
    x = np.arange(len(criteria))
    width = 0.25

    ax4.bar(x - width, df_summary['Min'], width, label='Min CV',
           color='lightblue', alpha=0.7)
    ax4.bar(x, df_summary['Mean'], width, label='Mean CV',
           color=MODEL_COLORS[model_name], alpha=0.7)
    ax4.bar(x + width, df_summary['Max'], width, label='Max CV',
           color='lightcoral', alpha=0.7)

    ax4.set_xlabel('Scoring Criteria', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Coefficient of Variation (%)', fontsize=11, fontweight='bold')
    ax4.set_title('Coefficient of Variation Statistics',
                 fontweight='bold', fontsize=12)
    ax4.set_xticks(x)
    ax4.set_xticklabels(df_summary['Criterion'], rotation=45, ha='right')
    ax4.legend(fontsize=10)
    ax4.grid(axis='y', alpha=0.3)

    # Main title
    fig.suptitle(f'{MODEL_NAMES[model_name]} - Detailed Reliability Analysis',
                fontsize=16, fontweight='bold', y=0.995)

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / f'{model_name}_detail.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Saved: {model_name}_detail.png")

    if show:
        plt.show()

    plt.close()
    return output_path
