"""
Nature Journal Quality Radar Charts
===================================

Creates publication-ready radar charts for cross-model LLM evaluation comparison.
Follows Nature figure guidelines: 183mm single-column width, Arial font,
SVG/PDF/TIFF export, editable text.

Figure Contract:
- Core claim: Cross-model evaluation consistency assessment
- Layout: 2x2 grid (4 models), 89mm per panel
- Export: SVG, PDF, 600 DPI TIFF
- Colors: 色盘.html palette (Twilight & Bonfire theme)

Usage:
    python -m visualization.visualize_radar_nature
"""

import io
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.transforms import offset_copy

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# =============================================================================
# Nature Journal Configuration
# =============================================================================

# Publication-quality matplotlib settings
mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",  # editable text in SVG
        "pdf.fonttype": 42,  # editable TrueType text in PDF
        "font.size": 7,  # Nature standard (6.5-7pt)
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "axes.labelsize": 7,
        "axes.titlesize": 9,
        "legend.fontsize": 6,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)

# Color palette from 色盘.html (Twilight & Bonfire theme)
FORMULA_COLORS_NATURE = {
    1: "#435485",  # Deep Indigo (深靛蓝) - Gel & GelMA
    2: "#7d5fad",  # Lavender (薰衣草) - PAM & Gel
    3: "#615a99",  # Starry Purple (星空紫) - CS & GelMA
    4: "#9e66a0",  # Mallow Purple (锦葵紫) - GelMA & Silk Fibroin
    5: "#f17554",  # Vibrant Orange (活力橙) - GelMA & PEG
    6: "#ffb03a",  # Warm Sun Yellow (暖阳黄) - Starch & GelMA
    7: "#c37b9f",  # Rose Pink (玫瑰粉紫) - Chitin & GelMA
    8: "#a8a2b9",  # Medium Gray Purple - GelMA & Cellulose
    9: "#37a294",  # Lake Pine Green (湖松绿) - PAM & PVA
    10: "#2c2a3a",  # Deep Charcoal Purple - PAM & PEG
}

# Formula names for legend
FORMULA_NAMES = {
    1: "Gel & GelMA",
    2: "PAM & Gel",
    3: "CS & GelMA",
    4: "GelMA & Silk Fibroin",
    5: "GelMA & PEG",
    6: "Starch & GelMA",
    7: "Chitin & GelMA",
    8: "GelMA & Cellulose",
    9: "PAM & PVA",
    10: "PAM & PEG",
}

# Display names for models
MODEL_DISPLAY_NAMES = {
    "gpt-5": "GPT-5",
    "grok-4": "Grok-4",
    "claude-opus-4-5-20251101": "Claude Opus 4.5",
    "gemini-3-pro-preview": "Gemini 3 Pro",
}

# 6 evaluation dimensions
DIMENSIONS = [
    "Mechanical_Safety",
    "Swelling_Performance",
    "Endothelialization",
    "SMC_inhibition",
    "Anti_inflammation",
    "Thrombogenicity",
]

# Dimension display names
DIMENSION_DISPLAY_NAMES = {
    "Mechanical_Safety": "Mechanical Safety",
    "Swelling_Performance": "Swelling Performance",
    "Endothelialization": "Endothelialization",
    "SMC_inhibition": "SMC Inhibition",
    "Anti_inflammation": "Anti-inflammation",
    "Thrombogenicity": "Thrombogenicity",
}

# =============================================================================
# Publication Export Functions
# =============================================================================


def save_nature_figure(fig, filename, dpi=600, include_png_preview=False):
    """
    Export figure in Nature journal formats: SVG, PDF, TIFF (600 DPI)

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure object to export
    filename : str
        Base filename (without extension)
    dpi : int
        DPI for TIFF output (default: 600 for Nature)
    include_png_preview : bool
        Whether to include low-DPI PNG for visual analysis
    """
    # SVG with editable text
    fig.savefig(f"{filename}.svg", bbox_inches="tight", format="svg")
    print(f"[OK] Saved: {filename}.svg (vector, editable text)")

    # PDF with editable text
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", format="pdf")
    print(f"[OK] Saved: {filename}.pdf (vector, editable text)")

    # TIFF at 600 DPI (Nature requirement)
    fig.savefig(f"{filename}.tiff", dpi=dpi, bbox_inches="tight", format="tiff")
    print(f"[OK] Saved: {filename}.tiff (600 DPI)")

    # Optional PNG preview for visual analysis
    if include_png_preview:
        fig.savefig(
            f"{filename}_preview.png", dpi=150, bbox_inches="tight", format="png"
        )
        print(f"[OK] Saved: {filename}_preview.png (150 DPI preview)")


# =============================================================================
# Radar Chart Creation
# =============================================================================


def create_single_radar_panel(ax, model_data, model_name):
    """
    Create a single radar panel for one model

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Polar axes object
    model_data : List[Dict]
        Model evaluation data
    model_name : str
        Model identifier
    """
    # Convert to DataFrame and aggregate by Formula
    df = pd.DataFrame(model_data)
    formula_means = df.groupby("Formula")[DIMENSIONS].mean()

    # Calculate angles for 6 dimensions
    angles = np.linspace(0, 2 * np.pi, len(DIMENSIONS), endpoint=False)
    angles_full = np.concatenate([angles, [angles[0]]])  # Complete the circle

    # Plot each formula
    for formula_num in range(1, 11):
        if formula_num not in formula_means.index:
            continue

        values = formula_means.loc[formula_num].values.tolist()
        values_full = values + [values[0]]  # Complete the circle

        color = FORMULA_COLORS_NATURE[formula_num]

        # Fill with low opacity
        ax.fill(angles_full, values_full, color=color, alpha=0.15, linewidth=0)
        # Stroke line
        ax.plot(angles_full, values_full, linewidth=1.2, color=color)

    # Set dimension labels
    ax.set_xticks(angles)
    ax.set_xticklabels(
        [DIMENSION_DISPLAY_NAMES[d] for d in DIMENSIONS],
        fontsize=6.5,
        fontweight="bold",
        color="black",
    )
    # add padding
    ax.tick_params(axis="x", which="major", pad=6)

    for label in ax.get_xticklabels():
        match label.get_text():
            case "Mechanical Safety":
                # 使用 transform 偏移（避免直接操作 position）
                trans = offset_copy(
                    label.get_transform(),
                    fig=ax.figure,
                    x=25,  # 额外的 padding（点）
                    y=0,
                    units="points",
                )
                label.set_transform(trans)
                label.set_horizontalalignment("right")
                print("Mechanical label transformed")
            case "SMC Inhibition":
                trans = offset_copy(
                    label.get_transform(),
                    fig=ax.figure,
                    x=-15,  # 额外的 padding（点）
                    y=0,
                    units="points",
                )
                label.set_transform(trans)
                label.set_horizontalalignment("left")
                print("SMC label transformed")
            case _:
                pass

    # For polar plots, adjust radial limit to ensure labels are visible
    # Set y-limit well above 10 to provide generous space for labels
    ax.set_ylim(0, 20)

    # Radial axis settings
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=4.5)
    ax.grid(True, linestyle="--", alpha=0.4, linewidth=0.5)

    # Panel title
    display_name = MODEL_DISPLAY_NAMES.get(model_name, model_name)
    ax.set_title(display_name, fontsize=8.5, fontweight="bold", pad=20)


def create_nature_2x2_figure(
    data_file="extracted_data.json",
    base_dir=".",
    output_prefix="nature_radar_comparison",
):
    """
    Create Nature-quality 2x2 grid figure with all 4 models

    Parameters
    ----------
    data_file : str
        Path to extracted data JSON file
    base_dir : str
        Base directory path
    output_prefix : str
        Output filename prefix
    """
    # Load data
    data_path = Path(base_dir) / data_file
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Model order for 2x2 grid
    model_order = [
        "gpt-5",
        "grok-4",
        "claude-opus-4-5-20251101",
        "gemini-3-pro-preview",
    ]

    # Create figure: 183mm x 183mm (Nature single-column)
    # Convert mm to inches: 183mm / 25.4 = 7.20 inches
    fig = plt.figure(figsize=(7.20, 7.20), dpi=300)

    # Create 2x2 subplots with polar projection
    # Increased spacing for better label separation
    gs = fig.add_gridspec(
        2, 2, hspace=0.45, wspace=0.7, left=0.11, right=0.94, top=0.94, bottom=0.09
    )

    axes = []
    positions = [
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    ]  # Top-left, top-right, bottom-left, bottom-right

    for idx, (model_name, pos) in enumerate(zip(model_order, positions)):
        if model_name not in data:
            print(f"[WARNING] Model {model_name} not found in data")
            continue

        ax = fig.add_subplot(gs[pos[0], pos[1]], polar=True)
        create_single_radar_panel(ax, data[model_name], model_name)
        axes.append(ax)

    # Add unified legend at the bottom
    # Collect legend handles
    from matplotlib.lines import Line2D

    legend_handles = []
    for formula_num in range(1, 11):
        color = FORMULA_COLORS_NATURE[formula_num]
        name = FORMULA_NAMES[formula_num]
        handle = Line2D([0], [0], color=color, linewidth=1.5, label=name)
        legend_handles.append(handle)

    # Add legend to the figure
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.01),
        ncol=5,
        fontsize=5,
        frameon=False,
        columnspacing=0.8,
        handletextpad=0.3,
    )

    # Export to Nature formats
    output_dir = Path(base_dir) / "visualizations"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / output_prefix

    save_nature_figure(fig, str(output_path), dpi=600, include_png_preview=True)

    plt.close(fig)
    print("[DONE] Nature-quality radar charts created")

    return str(output_path)


# =============================================================================
# Command Line Interface
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create Nature journal quality radar charts"
    )
    parser.add_argument(
        "--data-file",
        default="extracted_data.json",
        help="Path to extracted data JSON file",
    )
    parser.add_argument("--base-dir", default=".", help="Base directory path")
    parser.add_argument(
        "--output-prefix",
        default="nature_radar_comparison",
        help="Output filename prefix",
    )

    args = parser.parse_args()

    create_nature_2x2_figure(
        data_file=args.data_file,
        base_dir=args.base_dir,
        output_prefix=args.output_prefix,
    )
