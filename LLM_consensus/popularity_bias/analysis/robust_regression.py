"""
Rigorous Popularity Bias Analysis (No Bootstrap)

Scientific Methods:
1. Partial Correlation - Control for confounding variables
2. Robust Regression - Huber/RANSAC for outlier resistance

Priority: Scientific Rigor > Effectiveness > Simplicity
"""

import json
import logging
import os
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from scipy.stats import spearmanr
from sklearn.linear_model import HuberRegressor, RANSACRegressor, LinearRegression
import warnings

warnings.filterwarnings('ignore')

# Get logger
logger = logging.getLogger(__name__)


class RigorousBiasAnalyzer:
    """Analyzer with scientifically rigorous methods (no bootstrap)"""

    def __init__(
        self,
        project_root: str = None,
        data_dir: str = None,
        results_dir: str = None
    ):
        """
        Initialize the analyzer.

        Args:
            project_root: Root directory of the project (default: auto-detect)
            data_dir: Directory containing input data (default: <project_root>/popularity_bias/data)
            results_dir: Directory for output results (default: <project_root>/popularity_bias/results)
        """
        # Auto-detect project root if not provided
        if project_root is None:
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up to popularity_bias, then up to project root
            project_root = os.path.dirname(os.path.dirname(current_dir))

        self.project_root = project_root
        self.base_dir = os.path.join(project_root, "popularity_bias", "analysis")
        self.data_dir = data_dir or os.path.join(project_root, "popularity_bias", "data")
        self.output_dir = results_dir or os.path.join(project_root, "popularity_bias", "results")

        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # Load data
        self.formula_materials = self._load_formula_materials()
        self.extracted_data = self._load_extracted_data()

        # Score dimensions
        self.dimensions = [
            "Mechanical_Safety",
            "Swelling_Performance",
            "Endothelialization",
            "SMC_inhibition",
            "Anti_inflammation",
            "Thrombogenicity",
        ]

        # Load frequencies
        with open(os.path.join(self.data_dir, "relative_frequencies.json"), 'r', encoding='utf-8') as f:
            self.relative_frequencies = json.load(f)

    def _load_formula_materials(self) -> Dict:
        formula_materials_path = os.path.join(self.data_dir, "formula_materials.json")
        if not os.path.exists(formula_materials_path):
            # Try fallback location
            fallback_path = os.path.join(self.project_root, "database", "formula_materials.json")
            if os.path.exists(fallback_path):
                formula_materials_path = fallback_path
            else:
                raise FileNotFoundError(f"formula_materials.json not found in {self.data_dir} or {fallback_path}")

        with open(formula_materials_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_extracted_data(self) -> Dict:
        # Try data directory first
        extracted_data_path = os.path.join(self.data_dir, "extracted_data.json")
        if not os.path.exists(extracted_data_path):
            # Fallback to project root
            extracted_data_path = os.path.join(self.project_root, "extracted_data.json")

        with open(extracted_data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_partial_correlation(
        self,
        model: str,
        dimension: str,
        relative_frequencies: Dict[int, float]
    ) -> Tuple[float, float, bool]:
        """
        Calculate partial correlation controlling for other dimensions.

        Partial correlation measures the relationship between two variables
        while controlling for the effect of one or more other variables.
        """
        scores_df = pd.DataFrame(self.extracted_data[model])

        # Mean aggregation (Rule A: Denoise first)
        mean_df = scores_df.groupby('Formula')[self.dimensions].mean().reset_index()

        # Get dimension scores and frequencies
        y = mean_df[dimension].values
        x_freq = np.array([
            relative_frequencies.get(str(int(f)), relative_frequencies.get(f, 0.0))
            for f in mean_df['Formula']
        ])

        # Control for other dimensions (exclude Total_Score and current dimension)
        control_dims = [d for d in self.dimensions if d != dimension]

        if len(control_dims) == 0:
            # No control variables, use regular correlation
            rho, p_val = spearmanr(y, x_freq)
            needs_debias = bool(abs(rho) > 0.5 and p_val < 0.10)
            return rho, p_val, needs_debias

        # Calculate partial correlation
        # ρ(X,Y|Z) = (ρxy - ρxz * ρyz) / sqrt((1-ρxz²)(1-ρyz²))
        def partial_corr(X, Y, Z):
            """Partial correlation between X and Y controlling for Z"""
            rho_xy, _ = spearmanr(X, Y)
            rho_xz, _ = spearmanr(X, Z)
            rho_yz, _ = spearmanr(Y, Z)

            denominator = np.sqrt((1 - rho_xz**2) * (1 - rho_yz**2))

            if denominator < 1e-10:
                return 0.0, 1.0

            rho_xyz = (rho_xy - rho_xz * rho_yz) / denominator

            # Permutation test for p-value (more rigorous than asymptotic)
            n = len(X)
            n_perm = 1000
            rho_perm = []

            for _ in range(n_perm):
                perm_idx = np.random.permutation(n)
                X_perm = X[perm_idx]

                rho_xy_perm, _ = spearmanr(X_perm, Y)
                rho_xz_perm, _ = spearmanr(X_perm, Z)

                if denominator > 0:
                    rho_xyz_perm = (rho_xy_perm - rho_xz_perm * rho_yz) / denominator
                else:
                    rho_xyz_perm = 0.0
                rho_perm.append(rho_xyz_perm)

            # Two-tailed p-value
            p_val = (np.sum(np.abs(rho_perm) >= abs(rho_xyz)) + 1) / (n_perm + 1)

            return rho_xyz, p_val

        # Use average of other dimensions as control
        Z = mean_df[control_dims].mean(axis=1).values

        rho_partial, p_val = partial_corr(y, x_freq, Z)

        # Dual-criterion thresholding
        needs_debias = bool(abs(rho_partial) > 0.5 and p_val < 0.10)

        return rho_partial, p_val, needs_debias

    def apply_robust_regression_debias(
        self,
        scores_df: pd.DataFrame,
        relative_frequencies: Dict[int, float],
        dimension: str
    ) -> np.ndarray:
        """
        Apply robust regression debiasing using Huber regression.

        Huber loss is less sensitive to outliers than squared loss.
        """
        # Mean aggregation
        mean_df = scores_df.groupby('Formula')[self.dimensions].mean().reset_index()

        X = np.array([
            relative_frequencies.get(str(int(f)), relative_frequencies.get(f, 0.0))
            for f in mean_df['Formula']
        ]).reshape(-1, 1)
        y = mean_df[dimension].values

        # Method A: Huber Regression (epsilon=1.35 recommended)
        huber = HuberRegressor(epsilon=1.35, max_iter=1000)
        huber.fit(X, y)
        y_pred_huber = huber.predict(X)

        # Method B: RANSAC (more robust to outliers)
        ransac = RANSACRegressor(
            estimator=LinearRegression(),
            min_samples=5,
            residual_threshold=1.0,
            max_trials=1000
        )
        ransac.fit(X, y)
        y_pred_ransac = ransac.predict(X)

        # Use average of both robust methods (ensemble approach)
        y_pred = (y_pred_huber + y_pred_ransac) / 2

        # Mean-anchoring shift with robust prediction
        mean_y = np.mean(y)
        residuals = y - y_pred
        debiased = residuals + mean_y

        return np.clip(debiased, 0, 10)

    def run_rigorous_analysis(self):
        """Run full rigorous analysis for all models"""
        logger.info("=" * 80)
        logger.info("RIGOROUS BIAS ANALYSIS (No Bootstrap)")
        logger.info("Methods: Partial Correlation + Robust Regression")
        logger.info("=" * 80)

        models = list(self.extracted_data.keys())
        full_results = {}

        for model in models:
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"Analyzing model: {model}")
            logger.info("=" * 80)

            scores_df = pd.DataFrame(self.extracted_data[model])

            # Step 1: Partial Correlation Analysis
            logger.info("[Method 1] Partial Correlation Analysis...")
            correlation_results = {}

            for dimension in self.dimensions:
                rho, p_val, needs_debias = self.calculate_partial_correlation(
                    model, dimension, self.relative_frequencies
                )

                correlation_results[dimension] = {
                    'rho': float(rho),
                    'p_value': float(p_val),
                    'needs_debiasing': needs_debias,
                    'method': 'partial_correlation'
                }

                logger.info(
                    f"  {dimension}: ρ_partial={rho:.3f}, p={p_val:.3f}, "
                    f"Debias={'YES' if needs_debias else 'NO'}"
                )

            # Step 2: Robust Regression Debiasing
            logger.info("[Method 2] Robust Regression Debiasing...")
            mean_df = scores_df.groupby('Formula')[self.dimensions].mean().reset_index()
            mean_df['relative_freq'] = mean_df['Formula'].map(self.relative_frequencies)

            debiased_df = pd.DataFrame({'Formula': mean_df['Formula']})

            for dimension in self.dimensions:
                if correlation_results[dimension]['needs_debiasing']:
                    logger.info(f"  Applying Robust debias to {dimension}...")
                    debiased_scores = self.apply_robust_regression_debias(
                        scores_df, self.relative_frequencies, dimension
                    )
                    debiased_df[f'{dimension}_debiased'] = debiased_scores
                else:
                    debiased_df[f'{dimension}_debiased'] = mean_df[dimension].values

            # Recalculate total
            debiased_cols = [f'{d}_debiased' for d in self.dimensions]
            debiased_df['Total_Score_debiased'] = debiased_df[debiased_cols].sum(axis=1)

            # Step 3: Determine optimal formula
            optimal_idx = debiased_df['Total_Score_debiased'].idxmax()
            optimal_formula = int(debiased_df.loc[optimal_idx, 'Formula'])
            optimal_total = debiased_df.loc[optimal_idx, 'Total_Score_debiased']

            formula_name = self.formula_materials['formulas'][str(optimal_formula)]['name']

            logger.info(
                f"Optimal formula: {optimal_formula} ({formula_name}), "
                f"Total score: {optimal_total:.2f}"
            )

            # Get dimension scores
            dimension_scores = {}
            for dim in self.dimensions:
                dimension_scores[dim] = float(debiased_df.loc[optimal_idx, f'{dim}_debiased'])

            full_results[model] = {
                'correlation_results': correlation_results,
                'optimal_formula': {
                    'formula_id': optimal_formula,
                    'formula_name': formula_name,
                    'total_score': float(optimal_total),
                    'dimension_scores': dimension_scores
                }
            }

            # Save debiased scores
            debiased_path = os.path.join(self.output_dir, f'{model}_debiased_rigorous_v2.json')
            debiased_df.to_json(debiased_path, orient='records', indent=2, force_ascii=False)

        # Save summary
        summary = {
            'methods': [
                'Partial Correlation (controlling for other dimensions)',
                'Robust Regression (Huber + RANSAC ensemble)'
            ],
            'threshold': '|ρ_partial| > 0.5 AND p < 0.10 (Permutation test)',
            'results': full_results
        }

        summary_path = os.path.join(self.output_dir, 'rigorous_analysis_v2_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"Analysis complete! Results saved to: {self.output_dir}")
        logger.info("=" * 80)

        return full_results


def analyze_popularity_bias(
    project_root: str = None,
    data_dir: str = None,
    results_dir: str = None,
    configure_logging: bool = True
) -> Dict:
    """
    Convenience function to run popularity bias analysis.

    Args:
        project_root: Root directory of the project (default: auto-detect)
        data_dir: Directory containing input data (default: <project_root>/popularity_bias/data)
        results_dir: Directory for output results (default: <project_root>/popularity_bias/results)
        configure_logging: Whether to configure logging (default: True)

    Returns:
        Dictionary containing full analysis results
    """
    if configure_logging:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
            ],
        )

    analyzer = RigorousBiasAnalyzer(
        project_root=project_root,
        data_dir=data_dir,
        results_dir=results_dir
    )
    return analyzer.run_rigorous_analysis()


def main():
    """Main entry point for command line usage"""
    return analyze_popularity_bias()


if __name__ == "__main__":
    main()
