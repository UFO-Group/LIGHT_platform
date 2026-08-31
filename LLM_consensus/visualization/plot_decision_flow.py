"""
Decision Flow: Per-Run Variability and Debiasing Effects

Figure Contract:
--------------
Core conclusion: Debiasing alters the winner formula for 1 out of 4 LLM models (Gemini),
while revealing substantial per-run variability in GPT-5 (91% consistency), Grok-4 (64%),
and Claude (64%).

Figure archetype: quantitative grid - numerical comparison with raw data exposure

Target journal: Nature (main text figure)

Panel map:
  Panel i (hero): 4×11 decision matrix + aggregate column
    - Shows raw per-run winner for each model (11 runs)
    - Aggregate column displays majority winner with consistency percentage
    - Exposes hidden variability (Grok-4/Claude are mixed despite aggregate F4)

  Panel j (validation): Slope chart
    - Original → Debaised winner transition
    - Shows only Gemini changes despite 100% original consistency

Evidence hierarchy:
  - Hero evidence: Matrix reveals that aggregate winners hide substantial per-run variation
  - Validation evidence: Debiasing effect is visible in slope chart

Statistics:
  - Consistency %: GPT-5 91%, Grok-4 64%, Claude 64%, Gemini 100%
  - Sample size: n=11 runs per model
  - Changed models: 1/4 (Gemini)

Source data:
  - extracted_data.json (per-run original winners)
  - reliability_analysis_results.json (aggregate winners)
  - rigorous_analysis_v2_summary.json (debiased winners)

Image-integrity notes:
  - No image adjustments - pure data visualization
  - All per-run data visible (no selection bias)

Reviewer risk:
  - Medium: Reviewer may ask why per-run variability differs between models
  - Mitigation: All raw data exposed in matrix for full transparency

Target: Nature journal publication standard
Width: 158mm (1-column figure)
Height: 52mm
Font: 9pt Arial
"""

import io
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

# Fix UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# =============================================================================
# PUBLICATION CONFIGURATION
# =============================================================================

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 9.0,
        "axes.linewidth": 0.7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.spines.left": True,
        "axes.spines.bottom": True,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "axes.labelsize": 9.5,
        "axes.titlesize": 10,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
    }
)

# Figure dimensions
FIGURE_WIDTH_MM = 158
FIGURE_HEIGHT_MM = 52  # Standard height for 1-column Nature figure
MM_TO_INCH = 1.0 / 25.4

# Panel width ratios
WIDTH_RATIOS = [1.3, 1.0]


# =============================================================================
# COLOR SCHEME (unified method families)
# =============================================================================

# Model colors - symmetric auxiliary palette
MODEL_COLORS = {
    "gpt-5": "#142864",  # #1 - Deep blue (best)
    "claude-opus-4-5-20251101": "#38307c",  # #2 - Blue-purple
    "grok-4": "#b64858",  # #5 - Red
    "gemini-3-pro-preview": "#e65028",  # #6 - Orange-red
}

MODEL_NAMES = {
    "gpt-5": "GPT-5",
    "grok-4": "Grok-4",
    "claude-opus-4-5-20251101": "Claude\nOpus 4.5",
    "gemini-3-pro-preview": "Gemini\n3 Pro",
}


# Formula colors - neutral family with signal highlighting
def get_formula_colors() -> dict[float, str]:
    """Formula color scheme using project color palette"""
    return {
        1: "#D8D8D8",  # Neutral light
        2: "#A8A8A8",  # Neutral mid (F2)
        3: "#787878",  # Neutral dark (F3)
        4: "#7b7bff",  # Blue main (F4) - main palette
        5: "#f4aedc",  # Pink signal (F5) - main palette
        6: "#D8D8D8",
        7: "#D8D8D8",
        8: "#D8D8D8",
        9: "#D8D8D8",
        10: "#A0A0A0",  # Medium-light gray (F10) - distinct from F3
    }


# =============================================================================
# DATA LOADING
# =============================================================================


def load_data(base_dir: Path):
    """Load all required data files"""

    # Resolve to absolute path for cross-platform compatibility
    base_dir = base_dir.resolve()

    # Load aggregate winners
    reliability_path = base_dir / "reliability_analysis_results.json"
    debias_path = (
        base_dir / "popularity_bias" / "results" / "rigorous_analysis_v2_summary.json"
    )

    if not reliability_path.exists():
        raise FileNotFoundError(f"Cannot find reliability data: {reliability_path}")
    if not debias_path.exists():
        raise FileNotFoundError(f"Cannot find debias data: {debias_path}")

    with open(reliability_path, "r", encoding="utf-8") as f:
        reliability_data = json.load(f)

    with open(debias_path, "r", encoding="utf-8") as f:
        debias_data = json.load(f)

    # Extract winners
    original_winners = {}
    debiased_winners = {}

    for model in reliability_data.keys():
        orig = (
            reliability_data[model]
            .get("winner_consistency", {})
            .get("most_common_winner")
        )
        debiased = (
            debias_data["results"][model].get("optimal_formula", {}).get("formula_id")
        )
        original_winners[model] = orig
        debiased_winners[model] = debiased

    return original_winners, debiased_winners


def extract_per_run_sequences(base_dir: Path):
    """Extract real per-run winner sequences from extracted_data.json"""

    # Resolve to absolute path for cross-platform compatibility
    base_dir = base_dir.resolve()
    extracted_path = base_dir / "extracted_data.json"

    if not extracted_path.exists():
        raise FileNotFoundError(f"Cannot find extracted data: {extracted_path}")

    with open(extracted_path, "r", encoding="utf-8") as f:
        extracted_data = json.load(f)

    sequences = {}

    for model, records in extracted_data.items():
        df = pd.DataFrame(records)
        winners_per_run = df.groupby("Run")["Winner"].first()

        winners = []
        for run_id in range(11):
            if run_id in winners_per_run.index:
                winner = int(winners_per_run[run_id])
                winners.append(winner)
            else:
                winners.append(None)

        sequences[model] = winners

    return sequences


def calculate_consistency_stats(sequences):
    """Calculate consistency statistics for each model"""

    stats = {}
    for model, winners in sequences.items():
        counter = Counter(winners)
        majority_winner, majority_count = counter.most_common(1)[0]
        consistency_pct = (majority_count / len(winners)) * 100
        stats[model] = {
            "majority_winner": majority_winner,
            "majority_count": majority_count,
            "consistency_pct": consistency_pct,
            "total_runs": len(winners),
            "distribution": dict(counter),
        }

    return stats


# =============================================================================
# PLOTTING FUNCTIONS
# =============================================================================


def plot_matrix_with_aggregate(ax, sequences, aggregate_winners, consistency_stats):
    """
    Plot 4×11 decision matrix with aggregate column.

    Panel i - Hero evidence showing raw per-run variability.
    """

    formula_colors = get_formula_colors()
    models = list(sequences.keys())
    n_rows = len(models)
    n_cols = 11

    # Plot matrix cells (11 columns of runs)
    for i, model in enumerate(models):
        sequence = sequences[model]

        for j, formula_id in enumerate(sequence):
            if formula_id is None:
                continue
            color = formula_colors.get(formula_id, "#D8D8D8")

            rect = Rectangle(
                (j, i), 1, 1, facecolor=color, edgecolor="#FFFFFF", linewidth=0.5
            )
            ax.add_patch(rect)

    # Add aggregate column (column 11)
    agg_col = n_cols
    for i, model in enumerate(models):
        agg_winner = aggregate_winners[model]
        consistency = consistency_stats[model]["consistency_pct"]
        color = formula_colors.get(agg_winner, "#D8D8D8")

        # Draw aggregate cell
        rect = Rectangle(
            (agg_col, i), 2, 1, facecolor=color, edgecolor="black", linewidth=1.0
        )
        ax.add_patch(rect)

        # Add winner label with consistency percentage
        label = f"F{agg_winner}\n({int(consistency)}%)"
        ax.text(
            agg_col + 1,
            i + 0.5,
            label,
            ha="center",
            va="center",
            fontsize=7,
            color="white",
            fontweight="bold",
        )

        # Draw connecting line from last matrix column to aggregate
        last_col_x = n_cols - 0.5
        ax.plot(
            [last_col_x, agg_col],
            [i + 0.5, i + 0.5],
            color="gray",
            linewidth=1.0,
            alpha=0.5,
            zorder=0,
        )

    # Set axis properties
    ax.set_xlim(-0.5, agg_col + 2.7)
    ax.set_ylim(-0.2, n_rows + 1.5)
    # Note: set_aspect('equal') removed to prevent row height distortion

    # Labels
    ax.set_ylabel("Model", fontsize=9.5, fontweight="bold")
    ax.set_xticks([])

    # Y-axis labels (model names)
    ax.set_yticks(np.arange(n_rows) + 0.5)
    ax.set_yticklabels([MODEL_NAMES.get(m, m) for m in models], fontsize=8.5)

    # Shorten spine display range while keeping plot area height
    # This makes the axis look shorter while preserving space for legend
    ax.spines["left"].set_bounds((0, n_rows))  # Only show spine from 0 to 4
    ax.spines["bottom"].set_bounds(
        (-0.5, agg_col + 2)
    )  # Only show spine for heatmap width

    # Column annotations
    ax.text(
        n_cols / 2 - 0.5,
        -1,
        "Runs 1-11",
        ha="center",
        va="bottom",
        #  va="top",
        fontsize=8,
        style="italic",
    )
    ax.text(
        agg_col + 1,
        -1,
        "Majority",
        ha="center",
        va="bottom",
        fontsize=8,
        style="italic",
        fontweight="bold",
    )

    # Add color legend in top-right corner of heatmap
    # Show only formulas that appear in data: F3, F4, F5, F10 (F2 not shown)
    # Arrange in 2 columns × 2 rows layout, aligned to right edge of heatmap
    legend_formulas = [
        [3, 5],  # Left column: F3 (top), F5 (bottom)
        [4, 10],  # Right column: F4 (top), F10 (bottom)
    ]
    legend_box_size = 0.7
    legend_spacing = 0.15 * 3
    legend_x_start = agg_col + 0.3  # Position right after aggregate column
    legend_y_start = n_rows + legend_box_size + 0.2  # Near top of heatmap

    for col_idx, column_formulas in enumerate(legend_formulas):
        for row_idx, formula_id in enumerate(column_formulas):
            # Calculate position (2 columns, 2 rows)
            x_pos = legend_x_start + col_idx * (legend_box_size + legend_spacing) - 0.4
            y_pos = legend_y_start - row_idx * (legend_box_size + legend_spacing / 3)
            color = formula_colors.get(formula_id, "#D8D8D8")

            # Draw color box
            rect = Rectangle(
                (x_pos, y_pos),
                legend_box_size * 1.3,
                legend_box_size - 0.2,
                facecolor=color,
                edgecolor="black",
                linewidth=0.5,
            )
            ax.add_patch(rect)

            # Add formula label above box
            ax.text(
                x_pos,  # + legend_box_size / 2,
                #  y_pos + legend_box_size + 0.1,
                y_pos + 0.1,
                f"F{formula_id}",
                ha="left",
                va="bottom",
                fontsize=7,
                color="white",
            )


def plot_slope_chart(ax, original_winners, debiased_winners):
    """
    Plot slope chart showing original → debiased winners.

    Panel j - Validation evidence showing debiasing effects.
    """

    models = list(original_winners.keys())

    # Set up axis
    ax.set_xlim(0, 1.15)  # Extend x-axis to make room for right-side annotation
    ax.set_ylim(0, 11)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Original", "Debiased"], fontsize=8.5)
    ax.set_xlabel("Winner Formula", fontsize=9.5, fontweight="bold")

    # Y-axis (formula IDs)
    ax.set_yticks(range(1, 11))
    ax.set_yticklabels([f"F{i}" for i in range(1, 11)], fontsize=8)

    # Hide right spine (we'll add a custom axis on the far right)
    ax.spines["right"].set_visible(False)

    # Plot each model
    for i, model in enumerate(models):
        orig_y = original_winners[model]
        deb_y = debiased_winners[model]
        color = MODEL_COLORS.get(model, "#787878")

        # Draw connecting line (slope)
        # Add jitter for horizontal lines (F4→F4) to distinguish overlapping lines
        if orig_y == deb_y:
            # Horizontal line - add slight y-offset to separate overlapping lines
            # Order: Claude (teal, +0.15), Grok-4 (red, -0.15)
            if model == "claude-opus-4-5-20251101":
                jitter = 0.15
            elif model == "grok-4":
                jitter = -0.15
            else:
                jitter = 0.0
            ax.plot(
                [0, 1],
                [orig_y + jitter, deb_y + jitter],
                color=color,
                linewidth=2,
                alpha=0.7,
                zorder=2,
            )
        else:
            # Sloped line - no jitter
            ax.plot(
                [0, 1], [orig_y, deb_y], color=color, linewidth=2, alpha=0.7, zorder=2
            )

        # Draw points at jittered positions for horizontal lines
        if orig_y == deb_y:
            if model == "claude-opus-4-5-20251101":
                jitter = 0.15
            elif model == "grok-4":
                jitter = -0.15
            else:
                jitter = 0.0
            ax.scatter(
                0,
                orig_y + jitter,
                color=color,
                s=60,
                zorder=3,
                edgecolors="white",
                linewidths=0.5,
            )
            ax.scatter(
                1,
                deb_y + jitter,
                color=color,
                s=60,
                zorder=3,
                edgecolors="white",
                linewidths=0.5,
            )
        else:
            ax.scatter(
                0,
                orig_y,
                color=color,
                s=60,
                zorder=3,
                edgecolors="white",
                linewidths=0.5,
            )
            ax.scatter(
                1,
                deb_y,
                color=color,
                s=60,
                zorder=3,
                edgecolors="white",
                linewidths=0.5,
            )

        # Add labels only for changed models (Gemini)
        #  if orig_y != deb_y:
        #  ax.text(
        #  -0.08,
        #  orig_y,
        #  f"F{orig_y}",
        #  ha="right",
        #  va="center",
        #  fontsize=7,
        #  color="black",
        #  transform=ax.get_xaxis_transform(),
        #  )
        #  ax.text(
        #  1.08,
        #  deb_y,
        #  f"F{deb_y}",
        #  ha="left",
        #  va="center",
        #  fontsize=7,
        #  color="black",
        #  transform=ax.get_xaxis_transform(),
        #  )

    # Add right-side axis annotation for Gemini's F2 drop
    # Draw vertical axis line on right edge
    ax.axvline(x=1.12, color="black", linewidth=0.7, clip_on=False, zorder=1)

    # Add tick mark at F2 position (y=2)
    ax.plot([1.12, 1.14], [2, 2], color="black", linewidth=0.7, clip_on=False, zorder=1)

    # Add F2 label with bold text
    ax.text(
        1.145,
        2,
        "F2",
        ha="left",
        va="center",
        fontsize=8,
        fontweight="bold",
        color="black",
        clip_on=False,
    )

    # Optional: Add small annotation to highlight Gemini's unique drop
    # Find which model corresponds to Gemini
    gemini_model = None
    for model in models:
        if "gemini" in model.lower():
            gemini_model = model
            break

    if (
        gemini_model
        and original_winners[gemini_model] != debiased_winners[gemini_model]
    ):
        # Add subtle highlight annotation
        ax.annotate(
            "",
            xy=(1.02, debiased_winners[gemini_model]),
            xytext=(1.10, debiased_winners[gemini_model]),
            arrowprops=dict(
                arrowstyle="->",
                color=MODEL_COLORS.get(gemini_model, "#787878"),
                lw=1.0,
                alpha=0.6,
            ),
            annotation_clip=False,
        )


def connect_panels(fig, ax_matrix, ax_slope, models, original_winners):
    """Draw connecting lines from matrix aggregate column to slope chart"""

    n_cols = 11
    agg_col = n_cols
    agg_width = 2

    for i, model in enumerate(models):
        # Matrix aggregate cell RIGHT EDGE position
        # Aggregate cell spans from (agg_col, i) to (agg_col + agg_width, i + 1)
        # Right edge is at x = agg_col + agg_width, center y = i + 0.5
        matrix_x = agg_col + agg_width  # Right edge of aggregate cell
        matrix_y = i + 0.5  # Vertical center of the row

        # Slope chart original side position
        slope_y = original_winners[model]

        # Get figure coordinates
        matrix_coord = ax_matrix.transData.transform((matrix_x, matrix_y))
        slope_coord = ax_slope.transData.transform((0, slope_y))

        # Convert to figure coordinates
        matrix_fig = fig.transFigure.inverted().transform(matrix_coord)
        slope_fig = fig.transFigure.inverted().transform(slope_coord)

        # Draw connecting line
        color = MODEL_COLORS.get(model, "#787878")
        fig.add_artist(
            Line2D(
                [matrix_fig[0], slope_fig[0]],
                [matrix_fig[1], slope_fig[1]],
                transform=fig.transFigure,
                color=color,
                linewidth=1.5,
                alpha=0.6,
                zorder=1,
            )
        )


def save_publication_figure(fig, output_path: Path, dpi=600):
    """
    Save figure in Nature publication formats.

    Formats:
    - SVG (editable text, preferred for revision)
    - PDF (editable text, publication quality)
    - TIFF (Nature submission format, LZW compression)
    - PNG (raster backup, 600 DPI)
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # PNG (raster backup)
    fig.savefig(
        output_path.with_suffix(".png"),
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    print(f"[OK] Saved PNG: {output_path.with_suffix('.png')}")

    # PDF (publication quality)
    fig.savefig(
        output_path.with_suffix(".pdf"),
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    print(f"[OK] Saved PDF: {output_path.with_suffix('.pdf')}")

    # SVG (preferred for revision - editable text)
    fig.savefig(
        output_path.with_suffix(".svg"),
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    print(f"[OK] Saved SVG: {output_path.with_suffix('.svg')}")

    # TIFF (Nature submission format with LZW compression)
    fig.savefig(
        output_path.with_suffix(".tiff"),
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    print(f"[OK] Saved TIFF: {output_path.with_suffix('.tiff')}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main execution - generates publication-quality figure"""

    print("=" * 80)
    print("Decision Flow: Per-Run Variability and Debiasing Effects")
    print("=" * 80)

    # Load data - auto-detect project root
    print("\nLoading data...")

    # Get project root directory (parent of visualization/)
    base_dir = Path(__file__).resolve().parent.parent

    print(f"  Using project root: {base_dir}")

    original_winners, debiased_winners = load_data(base_dir)

    print("\nExtracting per-run sequences...")
    sequences = extract_per_run_sequences(base_dir)

    print("\nCalculating consistency statistics...")
    consistency_stats = calculate_consistency_stats(sequences)

    # Print summary
    print("\nPer-run winner distribution:")
    for model in original_winners.keys():
        stats = consistency_stats[model]
        model_short = model.split("-")[0].split(".")[0]
        dist_str = ", ".join(
            [f"F{f}:{c}x" for f, c in sorted(stats["distribution"].items())]
        )
        print(f"  {model_short:8s}: {dist_str}")
        print(
            f"           Majority: F{stats['majority_winner']} ({int(stats['consistency_pct'])}%)"
        )

    print("\nAggregate → Debiasing:")
    n_changed = 0
    for model in original_winners.keys():
        orig = original_winners[model]
        deb = debiased_winners[model]
        changed = "CHANGED" if orig != deb else "unchanged"
        model_short = model.split("-")[0].split(".")[0]
        print(f"  {model_short:8s}: F{orig} → F{deb} ({changed})")
        if orig != deb:
            n_changed += 1

    print(f"\nSummary: {n_changed}/4 models changed after debiasing")

    # Create figure
    print("\nGenerating publication figure...")
    fig_width = FIGURE_WIDTH_MM * MM_TO_INCH
    fig_height = FIGURE_HEIGHT_MM * MM_TO_INCH

    fig, (ax_matrix, ax_slope) = plt.subplots(
        1,
        2,
        figsize=(fig_width, fig_height),
        gridspec_kw={"width_ratios": WIDTH_RATIOS, "wspace": 0.3},
    )

    # Plot panels
    plot_matrix_with_aggregate(
        ax_matrix, sequences, original_winners, consistency_stats
    )

    plot_slope_chart(ax_slope, original_winners, debiased_winners)

    # Connect panels
    connect_panels(
        fig, ax_matrix, ax_slope, list(original_winners.keys()), original_winners
    )

    # Save figure
    output_path = Path(base_dir) / "visualizations" / "decision_flow"
    print(f"\nSaving figure to: {output_path}")
    save_publication_figure(fig, output_path, dpi=600)

    print("\nSUCCESS: Publication figure generated")
    print("\nFigure contract fulfilled:")
    print("  - Core conclusion: Debiasing alters 1/4 models (Gemini)")
    print("  - Per-run variability exposed in matrix")
    print("  - Consistency percentages displayed")
    print("  - Statistics: n=11 runs per model")

    plt.close(fig)


if __name__ == "__main__":
    main()
