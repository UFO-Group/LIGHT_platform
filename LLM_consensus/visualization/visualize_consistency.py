"""
Winner consistency visualization - Bar chart comparing decision consistency across models
"""

from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .visualize_utils import MODEL_COLORS, MODEL_NAMES, get_output_dir


def plot_winner_consistency(
    data: Dict, base_dir: str = ".", save: bool = True, show: bool = False
) -> Optional[Path]:
    """
    Plot decision consistency comparison across models

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

    consistency_data = []
    for model in models:
        wc = data[model]["winner_consistency"]
        if "error" not in wc:
            consistency_data.append(
                {
                    "Model": model,
                    "Consistency Rate (%)": wc["consistency_rate"],
                    "Most Common Winner": f"Formula {int(wc['most_common_winner'])}",
                    "Count": int(wc["most_common_count"]),
                }
            )

    df = pd.DataFrame(consistency_data)

    # Create chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left plot: Consistency rate bar chart
    colors = [MODEL_COLORS[model] for model in df["Model"]]
    bars = ax1.bar(
        range(len(df)),
        df["Consistency Rate (%)"],
        color=colors,
        alpha=0.8,
        edgecolor="black",
    )

    # Add value labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    # Add reference lines
    ax1.axhline(
        y=80, color="green", linestyle="--", alpha=0.5, label="Excellent (≥80%)"
    )
    ax1.axhline(y=60, color="orange", linestyle="--", alpha=0.5, label="Good (≥60%)")

    ax1.set_xlabel("Model", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Decision Consistency Rate (%)", fontsize=12, fontweight="bold")
    ax1.set_title(
        "Decision Consistency Rate Comparison", fontsize=12, fontweight="bold"
    )
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels([MODEL_NAMES[m] for m in df["Model"]])
    ax1.legend(fontsize=9)
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_ylim(0, 105)

    # Right plot: Winner distribution grouped bar chart
    # 首先收集所有配方编号
    all_formulas = set()
    for model in models:
        wc = data[model]["winner_consistency"]
        if "error" not in wc and "winner_distribution" in wc:
            dist = wc["winner_distribution"]
            all_formulas.update(dist.keys())

    if all_formulas:
        formulas_sorted = sorted(all_formulas)

        # 为每个模型在所有配方位置上画柱状图
        for i, model in enumerate(models):
            wc = data[model]["winner_consistency"]
            if "error" not in wc and "winner_distribution" in wc:
                dist = wc["winner_distribution"]
                # 获取该模型在所有配方上的计数，没有则为0
                counts = [dist.get(f, 0) for f in formulas_sorted]

                # 使用偏移避免重叠
                offset = (i - len(models) / 2 + 0.5) * 0.2
                x_pos = np.arange(len(formulas_sorted)) + offset

                ax2.bar(
                    x_pos,
                    counts,
                    width=0.18,
                    label=MODEL_NAMES[model],
                    color=MODEL_COLORS[model],
                    alpha=0.8,
                )

    ax2.set_xlabel("Winner Formula", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Count", fontsize=12, fontweight="bold")
    ax2.set_title("Winner Formula Distribution", fontsize=12, fontweight="bold")

    if all_formulas:
        ax2.set_xticks(np.arange(len(formulas_sorted)))
        ax2.set_xticklabels([f"F{f}" for f in formulas_sorted])
    ax2.legend(fontsize=9, loc="upper left")
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    output_path = None
    if save:
        output_dir = get_output_dir(base_dir)
        output_path = output_dir / "winner_consistency.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print("[OK] Saved: winner_consistency.png")

    if show:
        plt.show()

    plt.close()
    return output_path
