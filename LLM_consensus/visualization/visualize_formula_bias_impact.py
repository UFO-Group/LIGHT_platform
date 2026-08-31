"""
Formula Popularity Bias Impact Heatmap

This module visualizes the impact of popularity bias on each formula across
different LLM models. The heatmap shows the score difference between debiased
and original scores, indicating how much each formula was affected by bias.

Author: Claude Code
Date: 2026-05-23
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle


class FormulaBiasImpactHeatmap:
    """
    Generate heatmaps showing popularity bias impact on formulas.

    The heatmap displays:
    - Rows: LLM models
    - Columns: Formulas
    - Color: Score difference (debiased - original)

    Positive values indicate original score was undervalued due to bias.
    Negative values indicate original score was overvalued due to bias.
    """

    # Model name mappings for display
    MODEL_NAMES = {
        "gpt-5": "GPT-5",
        "grok-4": "Grok-4",
        "claude-opus-4-5-20251101": "Claude Opus 4.5",
        "gemini-3-pro-preview": "Gemini 3 Pro"
    }

    # Formula names for display
    FORMULA_NAMES = {
        1: "F1: Gel+GelMA",
        2: "F2: PAM+Gel",
        3: "F3: Chitosan+GelMA",
        4: "F4: GelMA+Silk",
        5: "F5: GelMA+PEG",
        6: "F6: Starch+GelMA",
        7: "F7: Chitin+GelMA",
        8: "F8: GelMA+Cellulose",
        9: "F9: PAM+PVA",
        10: "F10: PAM+PEG"
    }

    def __init__(self, project_root: str = None):
        """
        Initialize the heatmap visualizer.

        Args:
            project_root: Root directory of the project.
                        Defaults to current working directory.
        """
        if project_root is None:
            self.project_root = Path.cwd()
        else:
            self.project_root = Path(project_root)

        self.output_dir = self.project_root / "visualization" / "formula_bias_impact"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configure matplotlib
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.dpi'] = 100

        # Configure seaborn
        sns.set_style("whitegrid")

    def load_data(self) -> Tuple[Dict, Dict, Dict]:
        """
        Load raw and debiased data for all models.

        Returns:
            Tuple of (raw_data_dict, debiased_data_dict, formula_info)

        Raises:
            FileNotFoundError: If required data files are not found.
        """
        # Load raw extracted data
        raw_data_path = self.project_root / "extracted_data.json"
        if not raw_data_path.exists():
            raise FileNotFoundError(f"Raw data not found: {raw_data_path}")

        with open(raw_data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Load debiased data for each model
        debiased_data = {}
        analysis_dir = self.project_root / "analysis_strong_effect"

        for model in raw_data.keys():
            debiased_path = analysis_dir / f"{model}_debiased_rigorous_v2.json"
            if not debiased_path.exists():
                raise FileNotFoundError(f"Debiased data not found: {debiased_path}")

            with open(debiased_path, 'r', encoding='utf-8') as f:
                debiased_data[model] = json.load(f)

        # Load formula information
        formula_path = self.project_root / "database" / "formula_materials.json"
        with open(formula_path, 'r', encoding='utf-8') as f:
            formula_info = json.load(f)

        return raw_data, debiased_data, formula_info

    def calculate_mean_scores(self, raw_data: Dict) -> Dict[str, pd.DataFrame]:
        """
        Calculate mean scores for each formula from raw data.

        Args:
            raw_data: Raw data dictionary with model as key.

        Returns:
            Dictionary mapping model name to DataFrame with mean scores.
        """
        mean_scores = {}

        for model, runs in raw_data.items():
            df = pd.DataFrame(runs)
            # Group by formula and calculate mean (only numeric columns)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.drop('Formula')
            df_mean = df.groupby('Formula', as_index=False)[numeric_cols].mean()
            df_mean['Formula'] = df_mean['Formula'].astype(int)
            df_mean = df_mean.sort_values('Formula')
            mean_scores[model] = df_mean

        return mean_scores

    def calculate_bias_impact(
        self,
        raw_data: Dict,
        debiased_data: Dict
    ) -> pd.DataFrame:
        """
        Calculate the bias impact for each model-formula combination.

        Bias impact = debiased_score - original_score

        Args:
            raw_data: Raw data dictionary.
            debiased_data: Debiased data dictionary.

        Returns:
            DataFrame with bias impact matrix (models x formulas).
        """
        # Get mean scores from raw data
        mean_scores = self.calculate_mean_scores(raw_data)

        # Prepare impact matrix
        models = list(raw_data.keys())
        formulas = list(range(1, 11))

        impact_matrix = np.zeros((len(models), len(formulas)))

        for i, model in enumerate(models):
            df_raw = mean_scores[model]
            df_debiased = pd.DataFrame(debiased_data[model])

            for j, formula in enumerate(formulas):
                # Get original score
                original_row = df_raw[df_raw['Formula'] == formula]
                if len(original_row) > 0:
                    original_score = original_row['Total_Score'].values[0]
                else:
                    original_score = 0

                # Get debiased score
                debiased_row = df_debiased[df_debiased['Formula'] == formula]
                if len(debiased_row) > 0:
                    debiased_score = debiased_row['Total_Score_debiased'].values[0]
                else:
                    debiased_score = 0

                # Calculate impact
                impact_matrix[i, j] = debiased_score - original_score

        # Create DataFrame
        model_names = [self.MODEL_NAMES.get(m, m) for m in models]
        formula_names = [self.FORMULA_NAMES.get(f, f"F{f}") for f in formulas]

        impact_df = pd.DataFrame(
            impact_matrix,
            index=model_names,
            columns=formula_names
        )

        return impact_df

    def plot_bias_impact_heatmap(self, impact_df: pd.DataFrame) -> str:
        """
        Create and save the bias impact heatmap.

        Args:
            impact_df: DataFrame with bias impact values.

        Returns:
            Path to saved image.
        """
        fig, ax = plt.subplots(figsize=(14, 10))

        # Use diverging colormap (blue-white-red)
        cmap = sns.diverging_palette(240, 10, as_cmap=True)

        # Determine colorbar range symmetrically
        vmax = max(abs(impact_df.min().min()), abs(impact_df.max().max()))
        vmax = max(vmax, 5.0)  # Ensure minimum range for visibility

        # Plot heatmap
        sns.heatmap(
            impact_df,
            annot=True,
            fmt='.2f',
            cmap=cmap,
            vmin=-vmax,
            vmax=vmax,
            center=0,
            square=True,
            linewidths=1.5,
            cbar_kws={
                'label': 'Bias Impact (Debiased - Original)',
                'shrink': 0.8
            },
            ax=ax
        )

        # Add title and labels
        ax.set_title(
            'Popularity Bias Impact on Formula Scores\n'
            '(Positive = Undervalued, Negative = Overvalued)',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        ax.set_xlabel('Formula', fontsize=13, fontweight='bold')
        ax.set_ylabel('LLM Model', fontsize=13, fontweight='bold')

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')

        # Adjust layout
        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / "formula_bias_impact_heatmap.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] Bias impact heatmap saved: {output_path}")
        return str(output_path)

    def plot_absolute_bias_heatmap(self, impact_df: pd.DataFrame) -> str:
        """
        Create heatmap showing absolute bias magnitude.

        This visualization uses a single-color scale to show how much
        each formula was affected by bias, regardless of direction.

        Args:
            impact_df: DataFrame with bias impact values.

        Returns:
            Path to saved image.
        """
        fig, ax = plt.subplots(figsize=(14, 10))

        # Calculate absolute values
        abs_impact_df = impact_df.abs()

        # Use sequential colormap (light to dark)
        cmap = sns.color_palette("light:red", as_cmap=True)

        # Plot heatmap
        sns.heatmap(
            abs_impact_df,
            annot=True,
            fmt='.2f',
            cmap=cmap,
            vmin=0,
            vmax=abs_impact_df.max().max(),
            square=True,
            linewidths=1.5,
            cbar_kws={
                'label': 'Absolute Bias Impact |Debiased - Original|',
                'shrink': 0.8
            },
            ax=ax
        )

        # Add title and labels
        ax.set_title(
            'Absolute Magnitude of Popularity Bias Impact on Formulas',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        ax.set_xlabel('Formula', fontsize=13, fontweight='bold')
        ax.set_ylabel('LLM Model', fontsize=13, fontweight='bold')

        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        output_path = self.output_dir / "formula_bias_absolute_impact_heatmap.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] Absolute bias impact heatmap saved: {output_path}")
        return str(output_path)

    def plot_formula_ranking_change(
        self,
        raw_data: Dict,
        debiased_data: Dict
    ) -> str:
        """
        Visualize ranking changes before and after debiasing.

        Args:
            raw_data: Raw data dictionary.
            debiased_data: Debiased data dictionary.

        Returns:
            Path to saved image.
        """
        mean_scores = self.calculate_mean_scores(raw_data)

        models = list(raw_data.keys())
        model_names = [self.MODEL_NAMES.get(m, m) for m in models]

        # Calculate rankings
        rankings_before = {}
        rankings_after = {}

        for model in models:
            df_raw = mean_scores[model]
            df_debiased = pd.DataFrame(debiased_data[model])

            rankings_before[model] = df_raw.sort_values(
                'Total_Score', ascending=False
            )['Formula'].values
            rankings_after[model] = df_debiased.sort_values(
                'Total_Score_debiased', ascending=False
            )['Formula'].values

        # Create comparison table
        fig, ax = plt.subplots(figsize=(14, 8))

        # Hide axes
        ax.axis('tight')
        ax.axis('off')

        # Prepare table data
        table_data = []
        for i, model in enumerate(models):
            row = [model_names[i]]
            for rank, formula in enumerate(rankings_before[model], 1):
                # Find rank after debiasing
                rank_after = list(rankings_after[model]).index(formula) + 1
                delta = rank_after - rank
                delta_str = f"({delta:+d})" if delta != 0 else ""
                table_data.append([
                    model_names[i],
                    rank,
                    self.FORMULA_NAMES.get(formula, f"F{formula}"),
                    rank_after,
                    delta_str
                ])
            # Add separator row
            if i < len(models) - 1:
                table_data.append([""] * 5)

        # Create column labels
        columns = [
            'Model',
            'Original Rank',
            'Formula',
            'Debiased Rank',
            'Change'
        ]

        # Create table
        table = ax.table(
            cellText=table_data,
            colLabels=columns,
            cellLoc='center',
            loc='center',
            colWidths=[0.15, 0.12, 0.35, 0.12, 0.12]
        )

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # Add title
        ax.set_title(
            'Formula Ranking Changes After Debiasing',
            fontsize=16,
            fontweight='bold',
            pad=20
        )

        plt.tight_layout()

        output_path = self.output_dir / "formula_ranking_change_table.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] Ranking change table saved: {output_path}")
        return str(output_path)

    def generate_all_visualizations(self) -> List[str]:
        """
        Generate all visualizations.

        Returns:
            List of paths to saved images.
        """
        print("\n" + "=" * 80)
        print("Generating Formula Popularity Bias Impact Visualizations")
        print("=" * 80)

        # Load data
        print("\n[1/4] Loading data...")
        raw_data, debiased_data, formula_info = self.load_data()

        # Calculate bias impact
        print("[2/4] Calculating bias impact...")
        impact_df = self.calculate_bias_impact(raw_data, debiased_data)

        # Generate bias impact heatmap
        print("[3/4] Generating bias impact heatmap...")
        heatmap_path = self.plot_bias_impact_heatmap(impact_df)

        # Generate absolute bias heatmap
        print("Generating absolute bias impact heatmap...")
        abs_heatmap_path = self.plot_absolute_bias_heatmap(impact_df)

        # Generate ranking change table
        print("[4/4] Generating ranking change table...")
        ranking_path = self.plot_formula_ranking_change(raw_data, debiased_data)

        print(f"\n{'=' * 80}")
        print(f"All visualizations saved to: {self.output_dir}")
        print(f"{'=' * 80}")

        return [heatmap_path, abs_heatmap_path, ranking_path]


def main():
    """Main entry point."""
    visualizer = FormulaBiasImpactHeatmap()
    visualizer.generate_all_visualizations()


if __name__ == "__main__":
    main()