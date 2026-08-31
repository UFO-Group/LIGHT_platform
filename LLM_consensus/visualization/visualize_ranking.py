"""
Reliability ranking visualization - Horizontal bar chart showing overall reliability ranking of models
"""

from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .visualize_utils import MODEL_COLORS, MODEL_NAMES, get_output_dir


def plot_reliability_ranking(
    data: Dict, base_dir: str = ".", save: bool = True, show: bool = False
) -> Optional[Path]:
    """
    Plot reliability ranking chart based on comprehensive scores

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
    # Calculate comprehensive scores
    models = list(data.keys())
    scores = []

    for model in models:
        # CV score (lower is better, convert to score)
        avg_cv = np.mean(
            [s["overall_cv"] for s in data[model]["scoring_reliability"].values()]
        )
        cv_score = max(0, 100 - avg_cv * 2)

        # ICC score
        avg_icc = np.mean(list(data[model]["icc_scores"].values()))
        icc_score = avg_icc * 100

        # Decision consistency score
        winner_cons = data[model]["winner_consistency"]["consistency_rate"]

        # Overall score (weighted average)
        overall_score = cv_score * 0.3 + icc_score * 0.3 + winner_cons * 0.4

        scores.append(
            {
                "Model": model,
                "Scoring Consistency": cv_score,
                "Inter-rater Reliability": icc_score,
                "Decision Stability": winner_cons,
                "Overall Score": overall_score,
            }
        )

    df = pd.DataFrame(scores).sort_values("Overall Score", ascending=True)

    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(df))
    colors = [MODEL_COLORS[model] for model in df["Model"]]

    ax.barh(y_pos, df["Overall Score"], color=colors, alpha=0.8, edgecolor="black")

    # Add value labels
    for i, (idx, row) in enumerate(df.iterrows()):
        ax.text(
            row["Overall Score"] + 1,
            i,
            f"{row['Overall Score']:.1f}",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([MODEL_NAMES[m] for m in df["Model"]], fontsize=11)
    ax.set_xlabel("Overall Score", fontsize=12, fontweight="bold")
    ax.set_title(
        "LLM Model Reliability Ranking\n(Based on weighted average of scoring consistency, inter-rater reliability, and decision stability)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.3)

    # Add legend
    legend_text = "Scoring Weights:\n• Scoring Consistency: 30%\n• Inter-rater Reliability: 30%\n• Decision Stability: 40%"
    ax.text(
        0.98,
        0.05,
        legend_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.tight_layout()

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / "reliability_ranking.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print("[OK] Saved: reliability_ranking.png")

    if show:
        plt.show()

    plt.close()
    return output_path
