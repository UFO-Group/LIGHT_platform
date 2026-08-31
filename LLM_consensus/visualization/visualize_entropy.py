"""
Entropy analysis visualization - Bar chart and scatter plot showing decision uncertainty
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Optional
from pathlib import Path

from .visualize_utils import MODEL_COLORS, MODEL_NAMES, get_output_dir


def plot_entropy_analysis(
    data: Dict,
    base_dir: str = ".",
    save: bool = True,
    show: bool = False
) -> Optional[Path]:
    """
    Plot entropy analysis showing decision uncertainty and consistency relationship

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
    models = list(data.keys())

    entropy_data = []
    for model in models:
        wc = data[model]['winner_consistency']
        if 'error' not in wc:
            entropy_data.append({
                'Model': model,
                'Actual Entropy': wc['entropy'],
                'Max Entropy': wc['max_entropy'],
                'Consistency Rate': wc['consistency_rate']
            })

    df = pd.DataFrame(entropy_data)

    # Create chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left plot: Entropy value comparison
    x = np.arange(len(df))
    width = 0.35

    bars1 = ax1.bar(x - width/2, df['Actual Entropy'], width, label='Actual Entropy',
                   color='steelblue', alpha=0.8)
    bars2 = ax1.bar(x + width/2, df['Max Entropy'], width, label='Max Entropy',
                   color='lightgray', alpha=0.8)

    ax1.set_xlabel('Model', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Entropy Value', fontsize=12, fontweight='bold')
    ax1.set_title('Information Entropy Comparison\n(Lower values indicate more concentrated decisions)',
                 fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([MODEL_NAMES[m] for m in df['Model']], rotation=45, ha='right')
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=8)

    # Right plot: Consistency vs Entropy scatter plot
    for i, row in df.iterrows():
        ax2.scatter(row['Actual Entropy'], row['Consistency Rate'],
                  s=200, color=MODEL_COLORS[row['Model']],
                  alpha=0.7, edgecolor='black', label=MODEL_NAMES[row['Model']])
        ax2.annotate(MODEL_NAMES[row['Model']],
                    (row['Actual Entropy'], row['Consistency Rate']),
                    fontsize=9, xytext=(5, 5), textcoords='offset points')

    ax2.set_xlabel('Information Entropy', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Decision Consistency Rate (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Entropy vs Consistency Relationship\n(Lower entropy, higher consistency)',
                 fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Add trend line
    z = np.polyfit(df['Actual Entropy'], df['Consistency Rate'], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(df['Actual Entropy'].min(), df['Actual Entropy'].max(), 100)
    ax2.plot(x_trend, p(x_trend), "r--", alpha=0.5, linewidth=2, label='Trend Line')
    ax2.legend(fontsize=9)

    plt.tight_layout()

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / 'entropy_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[OK] Saved: entropy_analysis.png")

    if show:
        plt.show()

    plt.close()
    return output_path
