"""
Model-specific radar charts - Show all 10 formulas with 6 evaluation dimensions for each model
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path
from typing import List, Dict, Optional
import sys
import io

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from .visualize_utils import MODEL_NAMES, get_output_dir

# Formula colors from gpt-final.svg (色盘.html palette)
# Using lowercase hex codes to match SVG exactly
FORMULA_COLORS = {
    1: '#435485',   # Deep Indigo (深靛蓝) - Gel & GelMA
    2: '#7d5fad',   # Lavender (薰衣草) - PAM & Gel
    3: '#615a99',   # Starry Purple (星空紫) - CS & GelMA
    4: '#9e66a0',   # Mallow Purple (锦葵紫) - GelMA & Silk Fibroin
    5: '#f17554',   # Vibrant Orange (活力橙) - GelMA & PEG
    6: '#ffb03a',   # Warm Sun Yellow (暖阳黄) - Starch & GelMA
    7: '#c37b9f',   # Rose Pink (玫瑰粉紫) - Chitin & GelMA
    8: '#a8a2b9',   # Medium Gray Purple - GelMA & Cellulose
    9: '#37a294',   # Lake Pine Green (湖松绿) - PAM & PVA
    10: '#2c2a3a'   # Deep Charcoal Purple - PAM & PEG
}

# Formula names for legend (from SVG)
FORMULA_NAMES = {
    1: 'Gel & GelMA',
    2: 'PAM & Gel',
    3: 'CS & GelMA',
    4: 'GelMA & Silk Fibroin',
    5: 'GelMA & PEG',
    6: 'Starch & GelMA',
    7: 'Chitin & GelMA',
    8: 'GelMA & Cellulose',
    9: 'PAM & PVA',
    10: 'PAM & PEG'
}

# 6 evaluation dimensions for radar chart axes
DIMENSIONS = [
    'Mechanical_Safety',
    'Swelling_Performance',
    'Endothelialization',
    'SMC_inhibition',
    'Anti_inflammation',
    'Thrombogenicity'
]

# Dimension names for display
DIMENSION_NAMES = {
    'Mechanical_Safety': 'Mechanical Safety',
    'Swelling_Performance': 'Swelling Performance',
    'Endothelialization': 'Endothelialization',
    'SMC_inhibition': 'SMC Inhibition',
    'Anti_inflammation': 'Anti-inflammation',
    'Thrombogenicity': 'Thrombogenicity'
}


def _create_single_model_radar(
    model_data: List[Dict],
    model_name: str,
    output_dir: Path,
    save: bool = True,
    show: bool = False
) -> Optional[Path]:
    """
    Create radar chart for a single model showing all formulas

    Parameters
    ----------
    model_data : List[Dict]
        List of run data for the model
    model_name : str
        Name of the model
    output_dir : Path
        Output directory path
    save : bool
        Whether to save the figure
    show : bool
        Whether to display the figure

    Returns
    -------
    Optional[Path]
        Path to saved file if save=True, None otherwise
    """
    # Convert to DataFrame and aggregate by Formula
    df = pd.DataFrame(model_data)

    # Group by Formula and calculate mean across runs
    formula_means = df.groupby('Formula')[DIMENSIONS].mean()

    # Create radar chart (matching SVG style: 864x864pt = ~12x12 inches at 72dpi)
    fig = plt.figure(figsize=(12, 12), dpi=300)
    ax = fig.add_subplot(111, polar=True)

    # Calculate angles for 6 dimensions
    angles = np.linspace(0, 2 * np.pi, len(DIMENSIONS), endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])  # Complete the circle

    # Plot each formula as a line with fill (matching SVG style)
    for formula_num in range(1, 11):
        if formula_num not in formula_means.index:
            continue

        values = formula_means.loc[formula_num].values.tolist()
        values = values + [values[0]]  # Complete the circle

        color = FORMULA_COLORS[formula_num]
        formula_name = FORMULA_NAMES[formula_num]

        # Add fill with low opacity (matching SVG: opacity: 0.1)
        ax.fill(angles, values, color=color, alpha=0.1, linewidth=0)
        # Add stroke line (matching SVG: stroke-width: 2)
        ax.plot(angles, values, linewidth=2.0, color=color, label=formula_name)

    # Set labels and styling (matching SVG: font-weight 700, font-size 10px)
    ax.set_xticks(angles[:-1])
    # Add radial offset to labels to prevent overlap with chart
    ax.set_xticklabels([DIMENSION_NAMES[d] for d in DIMENSIONS], fontsize=10, fontweight='bold')
    # Increase distance of axis labels from center
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        # Adjust radial position (1.15 = 15% further out)
        label.set_position((angle, 1.15))

    # Set y-axis range [0, 10] with all tick labels (matching SVG: 0-10)
    ax.set_ylim(0, 10)
    ax.set_yticks(range(11))
    ax.set_yticklabels([str(i) for i in range(11)], fontsize=8, color='#808080')

    # Grid styling - use dashed lines for circular grids and solid for radial
    ax.grid(True, linestyle='dashed', color='#808080', alpha=0.7, linewidth=0.5)

    # Add padding around the plot to prevent label overlap
    plt.subplots_adjust(left=0.05, right=0.75, top=0.9, bottom=0.05)

    # Legend on right side (matching SVG layout)
    ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), fontsize=10, frameon=True)

    # Title (matching SVG: "GPT Advice" style, 15px bold)
    display_name = MODEL_NAMES.get(model_name, model_name)
    ax.set_title(f'{display_name} Advice', fontsize=15, fontweight='bold', pad=20)

    # Background
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    output_path = None
    if save:
        output_path = output_dir / f'{model_name}_radar.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[OK] Saved: {model_name}_radar.png")

    if show:
        plt.show()

    plt.close()
    return output_path


def plot_model_radar_charts(
    data_file: str = "extracted_data.json",
    base_dir: str = ".",
    save: bool = True,
    show: bool = False
) -> List[Path]:
    """
    Create radar charts for all models, showing all 10 formulas across 6 evaluation dimensions

    Parameters
    ----------
    data_file : str
        Path to extracted data JSON file (default: "extracted_data.json")
    base_dir : str
        Base directory path (default: current directory)
    save : bool
        Whether to save the figures (default: True)
    show : bool
        Whether to display the figures (default: False)

    Returns
    -------
    List[Path]
        List of paths to saved files
    """
    # Load data
    data_path = Path(base_dir) / data_file
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get output directory
    output_dir = get_output_dir(base_dir)

    # Create radar chart for each model
    saved_files = []
    for model_name in data.keys():
        model_data = data[model_name]
        output_path = _create_single_model_radar(
            model_data, model_name, output_dir, save=save, show=show
        )
        if output_path:
            saved_files.append(output_path)

    print(f"[DONE] Created {len(saved_files)} radar charts")
    return saved_files


if __name__ == "__main__":
    # Default: use extracted_data.json in current directory
    plot_model_radar_charts(
        data_file="extracted_data.json",
        base_dir=".",
        save=True,
        show=False
    )
