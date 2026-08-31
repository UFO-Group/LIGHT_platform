"""
Debiasing Analysis Heatmap Visualization Module

Generate heatmaps showing bias detection results across LLM models based on
rigorous_analysis_v2 partial correlation analysis
"""

import json
import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle

# Set default font
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False


class DebiasHeatmapVisualizer:
    """Debiasing heatmap visualizer"""

    def __init__(self, base_dir: str = None):
        """
        Initialize visualizer

        Args:
            base_dir: Project root directory (default: analysis_strong_effect)
        """
        if base_dir is None:
            # Get project root directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            self.base_dir = os.path.join(project_root, "analysis_strong_effect")
        else:
            self.base_dir = base_dir

        self.output_dir = self.base_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Scoring dimensions
        self.dimensions = [
            "Mechanical_Safety",
            "Swelling_Performance",
            "Endothelialization",
            "SMC_inhibition",
            "Anti_inflammation",
            "Thrombogenicity",
        ]

        # Dimension name mapping (for display)
        self.dimension_names_map = {
            "Mechanical_Safety": "Mechanical\nSafety",
            "Swelling_Performance": "Swelling\nPerformance",
            "Endothelialization": "Endothelial\n-ization",
            "SMC_inhibition": "SMC\nInhibition",
            "Anti_inflammation": "Anti-\ninflammation",
            "Thrombogenicity": "Thrombo-\ngenicity",
        }

        # Model name mapping
        self.model_names_map = {
            "gpt-5": "GPT-5",
            "grok-4": "Grok-4",
            "claude-opus-4-5-20251101": "Claude\nOpus 4.5",
            "gemini-3-pro-preview": "Gemini\n3 Pro",
        }

        # Set plot style
        sns.set_style("whitegrid")

    def load_rigorous_summary(self) -> Dict:
        """Load rigorous_analysis_v2_summary.json"""
        path = os.path.join(self.base_dir, "rigorous_analysis_v2_summary.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def plot_comprehensive_heatmap(self):
        """Plot comprehensive heatmap: bias status for all models and dimensions"""

        summary = self.load_rigorous_summary()
        models = summary["results"].keys()

        # Prepare data matrices
        model_names = [self.model_names_map.get(m, m) for m in models]
        dimension_names = [self.dimension_names_map[d] for d in self.dimensions]

        # Create correlation coefficient matrices
        rho_matrix = []
        p_value_matrix = []
        needs_debias_matrix = []

        for model in models:
            rho_row = []
            p_row = []
            debias_row = []
            for dim in self.dimensions:
                corr_result = summary["results"][model]["correlation_results"][dim]
                rho_row.append(corr_result["rho"])
                p_row.append(corr_result["p_value"])
                debias_row.append(1 if corr_result["needs_debiasing"] else 0)
            rho_matrix.append(rho_row)
            p_value_matrix.append(p_row)
            needs_debias_matrix.append(debias_row)

        rho_df = pd.DataFrame(rho_matrix, index=model_names, columns=dimension_names)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))

        # Define custom colormap
        cmap = sns.diverging_palette(240, 10, as_cmap=True)  # Blue-white-red

        # Plot heatmap
        sns.heatmap(
            rho_df,
            annot=True,
            fmt=".3f",
            cmap=cmap,
            vmin=-1,
            vmax=1,
            center=0,
            square=True,
            linewidths=1.5,
            cbar_kws={"label": "Partial Correlation Coefficient (rho)", "shrink": 0.8},
            ax=ax,
        )

        # Mark cells with significant bias
        for i, model in enumerate(models):
            for j, dim in enumerate(self.dimensions):
                corr_result = summary["results"][model]["correlation_results"][dim]
                needs_debias = corr_result["needs_debiasing"]
                rho = corr_result["rho"]
                p_value = corr_result["p_value"]

                if needs_debias:
                    # Significant bias: add thick border
                    rect = Rectangle(
                        (j, i), 1, 1, fill=False, edgecolor="red", linewidth=3
                    )
                    ax.add_patch(rect)

        ax.set_title(
            "LLM Popularity Bias Detection (Partial Correlation Analysis)",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        # Add legend explanation
        legend_text = (
            "Legend:\n"
            "  Red border = Significant bias (|rho| > 0.5, p < 0.10)\n"
            "  Blue = Negative correlation (higher popularity, lower score)\n"
            "  Red = Positive correlation (higher popularity, higher score)"
        )
        ax.text(
            1.15,
            0.8,
            legend_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="bottom",
            #  verticalalignment='center',
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
        )

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "debias_heatmap_comprehensive.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] Comprehensive heatmap saved: {output_path}")

        return output_path

    def plot_p_value_heatmap(self):
        """Plot p-value heatmap"""

        summary = self.load_rigorous_summary()
        models = summary["results"].keys()

        model_names = [self.model_names_map.get(m, m) for m in models]
        dimension_names = [self.dimension_names_map[d] for d in self.dimensions]

        # Create p-value matrix
        p_matrix = []
        for model in models:
            p_row = []
            for dim in self.dimensions:
                p_value = summary["results"][model]["correlation_results"][dim][
                    "p_value"
                ]
                p_row.append(p_value)
            p_matrix.append(p_row)

        p_df = pd.DataFrame(p_matrix, index=model_names, columns=dimension_names)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))

        # Use red to green colormap (lower p-value = more green = more significant)
        cmap = sns.diverging_palette(10, 120, as_cmap=True)  # Red-white-green

        sns.heatmap(
            p_df,
            annot=True,
            fmt=".3f",
            cmap=cmap,
            vmin=0,
            vmax=0.15,
            center=0.075,
            square=True,
            linewidths=1.5,
            cbar_kws={"label": "P-Value (Permutation Test)", "shrink": 0.8},
            ax=ax,
        )

        # Mark significant cells (p < 0.10)
        for i, model in enumerate(models):
            for j, dim in enumerate(self.dimensions):
                corr_result = summary["results"][model]["correlation_results"][dim]
                p_value = corr_result["p_value"]
                needs_debias = corr_result["needs_debiasing"]

                if needs_debias:
                    rect = Rectangle(
                        (j, i), 1, 1, fill=False, edgecolor="red", linewidth=3
                    )
                    ax.add_patch(rect)

        ax.set_title(
            "LLM Popularity Bias Detection - P-Values",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "debias_heatmap_pvalue.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] P-value heatmap saved: {output_path}")

        return output_path

    def plot_bias_summary_heatmap(self):
        """Plot bias summary heatmap (0/1 matrix)"""

        summary = self.load_rigorous_summary()
        models = summary["results"].keys()

        model_names = [self.model_names_map.get(m, m) for m in models]
        dimension_names = [self.dimension_names_map[d] for d in self.dimensions]

        # Create 0/1 matrix
        bias_matrix = []
        for model in models:
            bias_row = []
            for dim in self.dimensions:
                needs_debias = summary["results"][model]["correlation_results"][dim][
                    "needs_debiasing"
                ]
                bias_row.append(1 if needs_debias else 0)
            bias_matrix.append(bias_row)

        bias_df = pd.DataFrame(bias_matrix, index=model_names, columns=dimension_names)

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))

        # Use binary colormap
        cmap = sns.color_palette("light:coral", as_cmap=True)

        sns.heatmap(
            bias_df,
            annot=True,
            fmt="d",
            cmap=cmap,
            vmin=0,
            vmax=1,
            square=True,
            linewidths=2,
            cbar_kws={"label": "Bias Detection", "ticks": [0.25, 0.75]},
            ax=ax,
        )

        # Manually set colorbar tick labels
        cbar = ax.collections[0].colorbar
        cbar.ax.set_yticklabels(["No Bias", "Bias Detected"])

        ax.set_title(
            "LLM Popularity Bias Detection Summary (1=Bias, 0=No Bias)",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "debias_heatmap_summary.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] Bias summary heatmap saved: {output_path}")

        return output_path

    def plot_stacked_bias_chart(self):
        """Plot stacked bar chart: bias degree for each model"""

        summary = self.load_rigorous_summary()
        models = list(summary["results"].keys())
        model_names = [self.model_names_map.get(m, m) for m in models]

        # Count bias for each model
        bias_counts = []
        for model in models:
            count = 0
            for dim in self.dimensions:
                if summary["results"][model]["correlation_results"][dim][
                    "needs_debiasing"
                ]:
                    count += 1
            bias_counts.append(count)

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))

        x = np.arange(len(model_names))
        total = len(self.dimensions)

        # Plot stacked bar chart
        bars1 = ax.bar(
            x,
            bias_counts,
            label="Biased Dimensions",
            color="#FF6B6B",
            edgecolor="darkred",
            linewidth=2,
        )
        bars2 = ax.bar(
            x,
            [total - b for b in bias_counts],
            bottom=bias_counts,
            label="Unbiased Dimensions",
            color="#4ECDC4",
            edgecolor="teal",
            linewidth=2,
        )

        # Add value labels
        for bar, count in zip(bars1, bias_counts):
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height / 2.0,
                    f"{count}",
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                    color="white",
                )

        for bar, count in zip(bars2, [total - b for b in bias_counts]):
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bias_counts[list(bars2).index(bar)] + height / 2.0,
                    f"{height}",
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                    color="white",
                )

        ax.set_xlabel("LLM Model", fontsize=13, fontweight="bold")
        ax.set_ylabel("Number of Dimensions", fontsize=13, fontweight="bold")
        ax.set_title(
            "LLM Popularity Bias Comparison by Model",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(model_names, fontsize=11)
        ax.set_ylim(0, total + 0.5)
        ax.legend(loc="upper right", fontsize=11)
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "debias_stacked_chart.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] Stacked bar chart saved: {output_path}")

        return output_path

    def plot_dimension_bias_bar(self):
        """Plot bar chart: number of biased models for each dimension"""

        summary = self.load_rigorous_summary()
        models = list(summary["results"].keys())

        dimension_names = [self.dimension_names_map[d] for d in self.dimensions]

        # Count biased models for each dimension
        dim_bias_counts = []
        for dim in self.dimensions:
            count = 0
            for model in models:
                if summary["results"][model]["correlation_results"][dim][
                    "needs_debiasing"
                ]:
                    count += 1
            dim_bias_counts.append(count)

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))

        x = np.arange(len(dimension_names))
        total_models = len(models)

        bars = ax.bar(
            x,
            dim_bias_counts,
            color="#FF6B6B",
            edgecolor="darkred",
            linewidth=2,
            alpha=0.8,
        )

        # Add value labels
        for bar, count in zip(bars, dim_bias_counts):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.05,
                f"{count}/{total_models}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )

        ax.set_xlabel("Scoring Dimension", fontsize=13, fontweight="bold")
        ax.set_ylabel("Number of Models with Bias", fontsize=13, fontweight="bold")
        ax.set_title(
            "LLM Popularity Bias by Dimension", fontsize=16, fontweight="bold", pad=20
        )
        ax.set_xticks(x)
        ax.set_xticklabels(dimension_names, rotation=45, ha="right")
        ax.set_ylim(0, total_models + 1)
        ax.grid(axis="y", alpha=0.3)

        # Add reference line
        ax.axhline(
            y=total_models / 2,
            color="orange",
            linestyle="--",
            linewidth=2,
            label="Half of Models",
        )
        ax.legend(loc="upper right", fontsize=11)

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "debias_dimension_bar.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] Dimension bias bar chart saved: {output_path}")

        return output_path

    def plot_model_formula_pvalue_heatmap(self):
        """
        Plot model-formula p-value heatmap: number of biased dimensions for each model-formula combination

        This shows how many dimensions (out of 6) were affected by popularity bias for each formula.
        A higher number indicates more bias impact on that formula's evaluation.
        """

        summary = self.load_rigorous_summary()
        models = list(summary["results"].keys())
        model_names = [self.model_names_map.get(m, m) for m in models]

        # Formula names (1-10)
        formula_names = [f"Formula {i}" for i in range(1, 11)]

        # For each model, count how many dimensions need debiasing
        biased_dim_counts = {}
        for model in models:
            count = 0
            for dim in self.dimensions:
                if summary["results"][model]["correlation_results"][dim][
                    "needs_debiasing"
                ]:
                    count += 1
            biased_dim_counts[model] = count

        # Create matrix (models × formulas)
        # Note: For the same model, all formulas have the same biased dimension count
        # because bias detection is done per dimension, not per formula
        bias_matrix = []
        for model in models:
            # All formulas for this model have the same count
            row = [biased_dim_counts[model]] * 10
            bias_matrix.append(row)

        # Create DataFrame
        bias_df = pd.DataFrame(bias_matrix, index=model_names, columns=formula_names)

        # Create figure
        fig, ax = plt.subplots(figsize=(16, 8))

        # Use YlOrRd colormap (yellow-orange-red, red=more bias)
        cmap = sns.color_palette("YlOrRd", as_cmap=True)

        # Range: 0 to 6 (maximum possible biased dimensions)
        vmin, vmax = 0, 6

        # Plot heatmap
        sns.heatmap(
            bias_df,
            annot=True,
            fmt="d",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            square=True,
            linewidths=1.5,
            cbar_kws={"label": "Number of Biased Dimensions (out of 6)", "shrink": 0.8},
            ax=ax,
        )

        ax.set_title(
            "LLM Model vs Formula: Popularity Bias Impact (Number of Biased Dimensions)\n"
            "Higher values = more bias impact on formula evaluation",
            fontsize=14,
            fontweight="bold",
            pad=20,
        )

        ax.set_xlabel("Formula", fontsize=13, fontweight="bold")
        ax.set_ylabel("LLM Model", fontsize=13, fontweight="bold")

        # Add legend explanation
        legend_text = (
            "Interpretation:\n"
            "  Number = Count of dimensions (out of 6) affected by popularity bias\n"
            "  0 = No bias detected (all dimensions unbiased)\n"
            "  6 = All dimensions affected by popularity bias\n"
            "  Note: Bias is detected per dimension, so all formulas\n"
            "  for the same model show the same count"
        )
        ax.text(
            1.18,
            0.5,
            legend_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
        )

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "model_formula_pvalue_heatmap.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] Model-Formula p-value heatmap saved: {output_path}")

        return output_path

    def plot_model_formula_heatmap(self):
        """Plot model-formula heatmap: debiased total scores for each model-formula combination"""

        summary = self.load_rigorous_summary()
        models = list(summary["results"].keys())
        model_names = [self.model_names_map.get(m, m) for m in models]

        # Formula names (1-10)
        formula_names = [f"Formula {i}" for i in range(1, 11)]

        # Create score matrix (models × formulas)
        score_matrix = []
        optimal_formulas = {}

        for model in models:
            # Load debiased scores for this model
            debiased_file = os.path.join(
                self.base_dir, f"{model}_debiased_rigorous_v2.json"
            )

            if not os.path.exists(debiased_file):
                print(f"[WARNING] Debias file not found: {debiased_file}")
                # Fill with zeros if file not found
                score_matrix.append([0.0] * 10)
                optimal_formulas[model] = None
                continue

            with open(debiased_file, "r", encoding="utf-8") as f:
                debiased_data = json.load(f)

            # Extract Total_Score_debiased for each formula
            scores = []
            for entry in debiased_data:
                formula_id = int(entry["Formula"])
                total_score = entry["Total_Score_debiased"]
                scores.append(total_score)

            score_matrix.append(scores)

            # Get optimal formula from summary
            optimal_formulas[model] = summary["results"][model]["optimal_formula"][
                "formula_id"
            ]

        # Create DataFrame
        score_df = pd.DataFrame(score_matrix, index=model_names, columns=formula_names)

        # Create figure
        fig, ax = plt.subplots(figsize=(16, 8))

        # Use RdYlGn colormap (red-yellow-green, green=higher score)
        cmap = sns.color_palette("RdYlGn", as_cmap=True)

        # Calculate vmin and vmax from data (slightly padded)
        vmin = min(min(row) for row in score_matrix) - 2
        vmax = max(max(row) for row in score_matrix) + 2

        # Plot heatmap
        sns.heatmap(
            score_df,
            annot=True,
            fmt=".1f",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            square=True,
            linewidths=1.5,
            cbar_kws={"label": "Debiased Total Score", "shrink": 0.8},
            ax=ax,
        )

        # Mark optimal formulas with thick border
        for i, model in enumerate(models):
            optimal_id = optimal_formulas.get(model)
            if optimal_id is not None:
                # Convert formula_id to column index (0-based)
                col_idx = optimal_id - 1
                rect = Rectangle(
                    (col_idx, i), 1, 1, fill=False, edgecolor="red", linewidth=4
                )
                ax.add_patch(rect)

        ax.set_title(
            "LLM Model vs Formula Recommendation Heatmap (Debiased Scores)",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        ax.set_xlabel("Formula", fontsize=13, fontweight="bold")
        ax.set_ylabel("LLM Model", fontsize=13, fontweight="bold")

        # Add legend explanation
        legend_text = (
            "Legend:\n"
            "  Red border = Optimal formula for that model\n"
            "  Color scale: Green (high score) → Yellow → Red (low score)"
        )
        ax.text(
            1.18,
            0.5,
            legend_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
        )

        plt.tight_layout()

        output_path = os.path.join(self.output_dir, "model_formula_heatmap.png")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"[OK] Model-Formula heatmap saved: {output_path}")

        return output_path

    def generate_all_visualizations(self):
        """Generate all visualizations"""

        print("\n" + "=" * 80)
        print("Generating debiasing analysis heatmaps")
        print("=" * 80)

        # Generate various heatmaps and charts
        print(
            "\n[1/6] Comprehensive bias heatmap (partial correlation coefficients)..."
        )
        self.plot_comprehensive_heatmap()

        print("\n[2/6] P-value heatmap...")
        self.plot_p_value_heatmap()

        print("\n[3/6] Bias summary heatmap (0/1 matrix)...")
        self.plot_bias_summary_heatmap()

        print("\n[4/6] Model bias comparison chart...")
        self.plot_stacked_bias_chart()

        print("\n[5/6] Dimension bias distribution chart...")
        self.plot_dimension_bias_bar()

        print("\n[6/6] Model-Formula p-value heatmap (bias impact)...")
        self.plot_model_formula_pvalue_heatmap()

        print(f"\n{'=' * 80}")
        print(f"All visualizations saved to: {self.output_dir}")
        print(f"{'=' * 80}")


def main():
    """Main function"""
    # Set base_dir to the correct location containing the data files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "popularity_bias", "results")

    visualizer = DebiasHeatmapVisualizer(base_dir=data_dir)
    visualizer.generate_all_visualizations()


if __name__ == "__main__":
    main()
