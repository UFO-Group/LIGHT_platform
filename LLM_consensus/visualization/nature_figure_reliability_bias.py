"""
Nature-style multi-panel figure: LLM Reliability and Bias Analysis

This figure combines four key analyses:
- Panel A: CV Analysis (Coefficient of Variation)
- Panel B: ICC Analysis (Intraclass Correlation Coefficient)
- Panel C: Decision Consistency
- Panel D: Debias Heatmap (Popularity Bias Detection)

Target: Nature journal publication standard
"""

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle

# ============================================================================
# Publication-Quality Configuration
# ============================================================================
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none",          # editable text in SVG
    "pdf.fonttype": 42,              # editable TrueType text in PDF
    "font.size": 8,
    "axes.linewidth": 0.8,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "legend.frameon": False,
    "legend.fontsize": 7,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
})

# Model configuration - consistent with other project visualizations
MODEL_COLORS = {
    'gpt-5': '#FF6B6B',                      # Red (from visualize_utils.py)
    'grok-4': '#4ECDC4',                     # Teal (from visualize_utils.py)
    'claude-opus-4-5-20251101': '#45B7D1',   # Blue (from visualize_utils.py)
    'gemini-3-pro-preview': '#FFA07A'       # Orange (from visualize_utils.py)
}

MODEL_NAMES = {
    'gpt-5': 'GPT-5',
    'grok-4': 'Grok-4',
    'claude-opus-4-5-20251101': 'Claude\nOpus 4.5',
    'gemini-3-pro-preview': 'Gemini\n3 Pro'
}

# Criteria configuration
CRITERIA = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
            'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']

CRITERION_NAMES_SHORT = {
    'Mechanical_Safety': 'Mech.\nSafety',
    'Swelling_Performance': 'Swelling\nPerf.',
    'Endothelialization': 'Endothe-\nlialization',
    'SMC_inhibition': 'SMC\nInhib.',
    'Anti_inflammation': 'Anti-\ninflam.',
    'Thrombogenicity': 'Thrombo-\ngenicity',
    'Total_Score': 'Total\nScore'
}

# Debias dimensions (excluding Total_Score)
DEBIAS_DIMENSIONS = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
                    'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity']

DIMENSION_NAMES_SHORT = {
    'Mechanical_Safety': 'Mech.\nSafety',
    'Swelling_Performance': 'Swelling\nPerf.',
    'Endothelialization': 'Endothe-\nlialization',
    'SMC_inhibition': 'SMC\nInhib.',
    'Anti_inflammation': 'Anti-\ninflam.',
    'Thrombogenicity': 'Thrombo-\ngenicity'
}


# ============================================================================
# Data Loading
# ============================================================================
def load_data(base_dir: str = "."):
    """Load all required data files"""
    base_path = Path(base_dir)

    # Load reliability data (CV, ICC, Consistency)
    reliability_file = base_path / "reliability_analysis_results.json"
    with open(reliability_file, 'r', encoding='utf-8') as f:
        reliability_data = json.load(f)

    # Load debias data
    debias_file = base_path / "popularity_bias" / "results" / "rigorous_analysis_v2_summary.json"
    with open(debias_file, 'r', encoding='utf-8') as f:
        debias_data = json.load(f)

    return reliability_data, debias_data


# ============================================================================
# Panel A: CV Analysis
# ============================================================================
def plot_cv_analysis(ax, reliability_data):
    """Plot CV comparison bar chart"""

    models = list(reliability_data.keys())

    # Prepare data
    cv_data = []
    for model in models:
        for criterion in CRITERIA:
            if criterion in reliability_data[model]['scoring_reliability']:
                cv_data.append({
                    'Model': model,
                    'Criterion': criterion,
                    'CV': reliability_data[model]['scoring_reliability'][criterion]['overall_cv']
                })

    df = pd.DataFrame(cv_data)

    # Create grouped bar chart
    x = np.arange(len(CRITERIA))
    width = 0.18

    for i, model in enumerate(models):
        model_data = df[df['Model'] == model]['CV'].values
        offset = (i - len(models) / 2 + 0.5) * width
        ax.bar(x + offset, model_data, width,
               label=MODEL_NAMES[model], color=MODEL_COLORS[model], alpha=0.85)

    # Reference lines
    ax.axhline(y=10, color='green', linestyle='--', linewidth=1, alpha=0.6, label='Excellent (<10%)')
    ax.axhline(y=20, color='orange', linestyle='--', linewidth=1, alpha=0.6, label='Fair (≥20%)')

    ax.set_xlabel('Scoring Criteria', fontweight='bold')
    ax.set_ylabel('Coefficient of Variation (%)', fontweight='bold')
    ax.set_title('A. Measurement Reliability (CV)', fontweight='bold', loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels([CRITERION_NAMES_SHORT[c] for c in CRITERIA], rotation=0, ha='center')
    ax.legend(loc='upper right', fontsize=6, ncol=2)
    ax.grid(axis='y', alpha=0.3, linewidth=0.5)
    ax.set_ylim(0, 25)


# ============================================================================
# Panel B: ICC Analysis
# ============================================================================
def plot_icc_analysis(ax, reliability_data):
    """Plot ICC heatmap"""

    models = list(reliability_data.keys())

    # Create ICC matrix
    icc_matrix = pd.DataFrame(index=CRITERIA, columns=models)

    for model in models:
        for criterion in CRITERIA:
            if criterion in reliability_data[model]['icc_scores']:
                icc_matrix.loc[criterion, model] = reliability_data[model]['icc_scores'][criterion]

    icc_matrix = icc_matrix.astype(float)

    # Plot heatmap
    sns.heatmap(icc_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
               vmin=0, vmax=1, cbar_kws={'label': 'ICC Value', 'shrink': 0.8},
               linewidths=0.5, linecolor='white', ax=ax)

    ax.set_title('B. Scoring Consistency (ICC)', fontweight='bold', loc='left')
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Use short names for axes
    ax.set_yticklabels([CRITERION_NAMES_SHORT[c] for c in icc_matrix.index], rotation=0)
    ax.set_xticklabels([MODEL_NAMES[m] for m in icc_matrix.columns], rotation=0)

    # Remove x and y labels (they're in tick labels now)
    ax.set_xlabel('')
    ax.set_ylabel('')


# ============================================================================
# Panel C: Decision Consistency
# ============================================================================
def plot_consistency_analysis(ax, reliability_data):
    """Plot decision consistency comparison"""

    models = list(reliability_data.keys())

    consistency_data = []
    for model in models:
        wc = reliability_data[model]["winner_consistency"]
        if "error" not in wc:
            consistency_data.append({
                "Model": model,
                "Consistency": wc["consistency_rate"],
                "Winner": int(wc['most_common_winner'])
            })

    df = pd.DataFrame(consistency_data)

    # Bar chart
    x = np.arange(len(df))
    colors = [MODEL_COLORS[model] for model in df["Model"]]
    bars = ax.bar(x, df["Consistency"], color=colors, alpha=0.85, edgecolor='black', linewidth=0.8)

    # Add value labels
    for i, (bar, consistency) in enumerate(zip(bars, df["Consistency"])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height,
                f"{consistency:.1f}%", ha='center', va='bottom', fontsize=7, fontweight='bold')

    # Reference lines
    ax.axhline(y=80, color='green', linestyle='--', linewidth=1, alpha=0.6)
    ax.axhline(y=60, color='orange', linestyle='--', linewidth=1, alpha=0.6)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Decision Consistency (%)', fontweight='bold')
    ax.set_title('C. Decision-Making Stability', fontweight='bold', loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_NAMES[m] for m in df["Model"]], rotation=0)
    ax.grid(axis='y', alpha=0.3, linewidth=0.5)
    ax.set_ylim(0, 105)

    # Add reference line labels
    ax.text(0.02, 0.95, '≥80%: Excellent', transform=ax.transAxes, fontsize=6,
            color='green', verticalalignment='top')
    ax.text(0.02, 0.72, '≥60%: Good', transform=ax.transAxes, fontsize=6,
            color='orange', verticalalignment='top')


# ============================================================================
# Panel D: Debias Heatmap
# ============================================================================
def plot_debias_heatmap(ax, debias_data):
    """Plot popularity bias detection heatmap"""

    models = list(debias_data["results"].keys())

    # Prepare data matrices
    model_names = [MODEL_NAMES[m] for m in models]
    dimension_names = [DIMENSION_NAMES_SHORT[d] for d in DEBIAS_DIMENSIONS]

    # Create correlation coefficient matrix
    rho_matrix = []
    for model in models:
        rho_row = []
        for dim in DEBIAS_DIMENSIONS:
            corr_result = debias_data["results"][model]["correlation_results"][dim]
            rho_row.append(corr_result["rho"])
        rho_matrix.append(rho_row)

    rho_df = pd.DataFrame(rho_matrix, index=model_names, columns=dimension_names)

    # Define custom colormap (diverging)
    cmap = sns.diverging_palette(240, 10, as_cmap=True)

    # Plot heatmap
    sns.heatmap(rho_df, annot=True, fmt=".2f", cmap=cmap,
                vmin=-1, vmax=1, center=0,
                linewidths=1, linecolor='white',
                cbar_kws={"label": "Partial Correlation (ρ)", "shrink": 0.8},
                ax=ax)

    # Mark cells with significant bias
    for i, model in enumerate(models):
        for j, dim in enumerate(DEBIAS_DIMENSIONS):
            corr_result = debias_data["results"][model]["correlation_results"][dim]
            needs_debias = corr_result["needs_debiasing"]

            if needs_debias:
                rect = Rectangle((j, i), 1, 1, fill=False,
                                edgecolor='red', linewidth=3)
                ax.add_patch(rect)

    ax.set_title('D. Popularity Bias Detection', fontweight='bold', loc='left')
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Add legend for red border
    legend_text = "Red border: Significant bias (|ρ|>0.5, p<0.10)"
    ax.text(0.5, -0.15, legend_text, transform=ax.transAxes,
            fontsize=6, ha='center', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.3))


# ============================================================================
# Main Figure Generation
# ============================================================================
def create_nature_figure(base_dir: str = "."):
    """Create the complete Nature-style multi-panel figure"""

    # Load data
    reliability_data, debias_data = load_data(base_dir)

    # Create figure with 2x2 grid
    fig = plt.figure(figsize=(12, 10))

    # Grid specification with adjusted spacing
    gs = fig.add_gridspec(2, 2, hspace=0.30, wspace=0.25,
                           left=0.08, right=0.95, top=0.94, bottom=0.06)

    # Panel A: CV Analysis (top-left)
    ax_a = fig.add_subplot(gs[0, 0])
    plot_cv_analysis(ax_a, reliability_data)

    # Panel B: ICC Analysis (top-right)
    ax_b = fig.add_subplot(gs[0, 1])
    plot_icc_analysis(ax_b, reliability_data)

    # Panel C: Decision Consistency (bottom-left)
    ax_c = fig.add_subplot(gs[1, 0])
    plot_consistency_analysis(ax_c, reliability_data)

    # Panel D: Debias Heatmap (bottom-right)
    ax_d = fig.add_subplot(gs[1, 1])
    plot_debias_heatmap(ax_d, debias_data)

    # Add overall figure title
    fig.suptitle('LLM Consensus: Reliability and Bias Analysis',
                 fontsize=14, fontweight='bold', y=0.98)

    return fig


def save_publication_figure(fig, output_path: Path, dpi=300):
    """Save figure in multiple publication-ready formats"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # PNG (high resolution)
    fig.savefig(output_path.with_suffix('.png'), dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved PNG: {output_path.with_suffix('.png')}")

    # PDF (vector, editable text)
    fig.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved PDF: {output_path.with_suffix('.pdf')}")

    # SVG (vector, fully editable)
    fig.savefig(output_path.with_suffix('.svg'), bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved SVG: {output_path.with_suffix('.svg')}")

    # TIFF (print-ready)
    fig.savefig(output_path.with_suffix('.tiff'), dpi=600, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"[OK] Saved TIFF: {output_path.with_suffix('.tiff')}")


def main():
    """Main execution"""

    print("\n" + "=" * 80)
    print("Creating Nature-style multi-panel figure: LLM Reliability and Bias Analysis")
    print("=" * 80 + "\n")

    # Get base directory (script location)
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    # Create figure
    print("[1/2] Generating figure...")
    fig = create_nature_figure(base_dir)

    # Save figure
    output_path = Path(base_dir) / "visualizations" / "nature_figure_reliability_bias"
    print(f"\n[2/2] Saving figure to: {output_path}")
    save_publication_figure(fig, output_path, dpi=300)

    plt.close(fig)

    print("\n" + "=" * 80)
    print("Figure generation complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
