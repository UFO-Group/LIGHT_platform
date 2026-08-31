"""
LLM Consensus Reliability Analysis
Analyzing scoring reliability of the same AI model across multiple runs
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
import sys
import io

# Set stdout to UTF-8 encoding (fixes Windows encoding issues)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class LLMReliabilityAnalyzer:
    """Analyzes reliability of LLM model across multiple runs"""

    def __init__(self, base_dir: str = ".", data_file: str = "extracted_data.json"):
        self.base_dir = Path(base_dir)
        self.data_file = data_file
        self.models = ["gpt-5", "grok-4", "claude-opus-4-5-20251101", "gemini-3-pro-preview"]
        self.criteria = [
            "Mechanical_Safety",
            "Swelling_Performance",
            "Endothelialization",
            "SMC_inhibition",
            "Anti_inflammation",
            "Thrombogenicity",
            "Total_Score"
        ]
        self.all_data = {}  # Stores raw data for all models
        self.analysis_results = {}  # Stores analysis results

    def load_data_from_json(self, json_file: str) -> Dict[str, pd.DataFrame]:
        """
        Load extracted data from JSON file

        Args:
            json_file: JSON file path

        Returns:
            Dictionary with model names as keys and DataFrames as values
        """
        file_path = self.base_dir / json_file

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        all_data = {}
        for model_name, records in data.items():
            df = pd.DataFrame(records)
            all_data[model_name] = df

        return all_data

    def load_all_data(self) -> None:
        """
        Load data for all models

        Loads data from pre-extracted JSON files
        """
        print("=" * 80)
        print("Step 1: Loading data")
        print("=" * 80)

        self.all_data = self.load_data_from_json(self.data_file)

        for model, df in self.all_data.items():
            print(f"\n{model}:")
            print(f"  ✓ Successfully loaded {len(df)} records, {df['Run'].nunique()} runs")

            # Check Winner field
            if 'Winner' in df.columns:
                winner_counts = df[df['Winner'].notna()].groupby('Run')['Winner'].first()
                print(f"  - Extracted {len(winner_counts)} winning formulas")
            else:
                print(f"  ⚠ Warning: Missing Winner column")

        print(f"\nTotal loaded data from {len(self.all_data)} models")

    def calculate_reliability_metrics(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Calculate reliability metrics

        Calculates the following metrics for each evaluation criterion:
        - Coefficient of Variation (CV): Standard deviation / Mean × 100%
        - Standard Deviation (Std)
        - Range
        - Consistency Ratio

        Args:
            df: DataFrame containing data from multiple runs

        Returns:
            Dictionary with criterion names as keys and dictionaries containing statistical metrics as values
        """
        results = {}

        # Group by runs and formulas
        for criterion in self.criteria:
            criterion_data = []

            for run_num in sorted(df['Run'].unique()):
                run_data = df[df['Run'] == run_num]

                for formula_num in range(1, 11):
                    formula_data = run_data[run_data['Formula'] == formula_num]

                    if not formula_data.empty and criterion in formula_data.columns:
                        value = formula_data[criterion].values[0]
                        if not pd.isna(value):
                            criterion_data.append({
                                'Run': run_num,
                                'Formula': formula_num,
                                'Value': value
                            })

            if not criterion_data:
                continue

            criterion_df = pd.DataFrame(criterion_data)

            # Calculate statistics for each formula across all runs
            formula_stats = []
            for formula_num in range(1, 11):
                formula_data = criterion_df[criterion_df['Formula'] == formula_num]['Value'].values

                if len(formula_data) > 1:
                    stats_dict = {
                        'Formula': formula_num,
                        'Mean': np.mean(formula_data),
                        'Std': np.std(formula_data, ddof=1),
                        'CV': np.std(formula_data, ddof=1) / np.mean(formula_data) * 100,
                        'Min': np.min(formula_data),
                        'Max': np.max(formula_data),
                        'Range': np.max(formula_data) - np.min(formula_data),
                        'N': len(formula_data)
                    }
                    formula_stats.append(stats_dict)

            if formula_stats:
                stats_df = pd.DataFrame(formula_stats)

                # Calculate overall reliability metrics
                results[criterion] = {
                    'formula_stats': stats_df,
                    'overall_cv': stats_df['CV'].mean(),
                    'overall_std': stats_df['Std'].mean(),
                    'max_cv': stats_df['CV'].max(),
                    'min_cv': stats_df['CV'].min(),
                    'consistency_ratio': (stats_df['Range'] / stats_df['Mean']).mean()
                }

        return results

    def calculate_icc(
        self,
        df: pd.DataFrame,
        criterion: str,
        icc_type: str = 'ICC3'
    ) -> Optional[float]:
        """
        Calculate Intraclass Correlation Coefficient (ICC) - evaluate inter-rater consistency

        Based on Shrout & Fleiss (1979) method:
        - ICC(1,1): One-way random effects model, single measurement
        - ICC(2,1): Two-way random effects model, single measurement, consistency
        - ICC(3,1): Two-way fixed effects model, single measurement, absolute agreement
        - ICC(3,k): Two-way fixed effects model, average measurement, absolute agreement

        Args:
            df: DataFrame containing data from multiple runs
            criterion: Evaluation criterion to analyze
            icc_type: ICC type, defaults to 'ICC3' (two-way fixed effects, absolute agreement)

        Returns:
            ICC value, ranging from -1 to 1, closer to 1 indicates better consistency
            None: Insufficient data to calculate
        """
        data_matrix = []

        for run_num in sorted(df['Run'].unique()):
            run_data = df[df['Run'] == run_num].sort_values('Formula')

            if criterion in run_data.columns:
                scores = run_data[criterion].values
                if len(scores) == 10 and not any(np.isnan(scores)):
                    data_matrix.append(scores)

        if len(data_matrix) < 2:
            return None

        data_matrix = np.array(data_matrix)
        n_raters = data_matrix.shape[0]  # Number of raters (runs)
        n_targets = data_matrix.shape[1]  # Number of targets (formulas)

        # Calculate ICC using two-way ANOVA method
        return self._calculate_icc_anova(data_matrix, icc_type)

    def _calculate_icc_anova(
        self,
        data_matrix: np.ndarray,
        icc_type: str = 'ICC3'
    ) -> Optional[float]:
        """
        Calculate ICC using ANOVA method

        Args:
            data_matrix: Score matrix with shape (n_raters, n_targets)
            icc_type: ICC type

        Returns:
            ICC value or None (if calculation fails)
        """
        if data_matrix.size == 0:
            return None

        n_raters = data_matrix.shape[0]
        n_targets = data_matrix.shape[1]

        # Calculate grand mean
        grand_mean = np.mean(data_matrix)

        # Calculate between-targets sum of squares
        target_means = np.mean(data_matrix, axis=0)
        ss_between_targets = n_raters * np.sum((target_means - grand_mean) ** 2)
        df_between_targets = n_targets - 1

        # Calculate between-raters sum of squares
        rater_means = np.mean(data_matrix, axis=1)
        ss_between_raters = n_targets * np.sum((rater_means - grand_mean) ** 2)
        df_between_raters = n_raters - 1

        # Calculate total sum of squares
        ss_total = np.sum((data_matrix - grand_mean) ** 2)

        # Calculate error sum of squares (residual)
        ss_error = ss_total - ss_between_targets - ss_between_raters
        df_error = (n_targets - 1) * (n_raters - 1)

        # Calculate mean squares
        ms_between_targets = ss_between_targets / df_between_targets if df_between_targets > 0 else 0
        ms_between_raters = ss_between_raters / df_between_raters if df_between_raters > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0

        # Calculate ICC based on Shrout & Fleiss (1979) formulas
        if icc_type == 'ICC1':
            # One-way random effects model, single measurement
            if ms_between_targets + (n_raters - 1) * ms_error == 0:
                return None
            icc = (ms_between_targets - ms_error) / (
                ms_between_targets + (n_raters - 1) * ms_error
            )

        elif icc_type == 'ICC2':
            # Two-way random effects model, single measurement, consistency
            denominator = (
                ms_between_targets
                + (n_raters - 1) * ms_error
                + n_raters * (ms_between_raters - ms_error) / n_targets
            )
            if denominator == 0:
                return None
            icc = (ms_between_targets - ms_error) / denominator

        elif icc_type == 'ICC3':
            # Two-way fixed effects model, single measurement, absolute agreement
            if ms_between_targets + (n_raters - 1) * ms_error == 0:
                return None
            icc = (ms_between_targets - ms_error) / (
                ms_between_targets + (n_raters - 1) * ms_error
            )

        elif icc_type == 'ICC3k':
            # Two-way fixed effects model, average measurement, absolute agreement
            if ms_between_targets == 0:
                return None
            icc = (ms_between_targets - ms_error) / ms_between_targets

        else:
            return None

        # ICC value should theoretically be in [-1, 1] range
        # May exceed due to numerical errors, needs truncation
        icc = max(min(icc, 1.0), -1.0)

        return icc

    def analyze_winner_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze winner formula consistency

        Calculates the following metrics:
        - Winner formula distribution
        - Most common winner formula
        - Consistency rate (proportion of most common winner)
        - Entropy (measures uncertainty in winner selection)
        - Maximum entropy (entropy value when all formulas appear with equal probability)

        Args:
            df: DataFrame containing Winner column

        Returns:
            Dictionary containing consistency analysis results
        """
        if 'Winner' not in df.columns:
            return {
                'error': 'Missing Winner column',
                'winner_distribution': {},
                'most_common_winner': None,
                'consistency_rate': 0.0,
                'entropy': 0.0,
                'max_entropy': 0.0
            }

        # Filter out records where Winner is NaN
        valid_df = df[df['Winner'].notna()]

        if valid_df.empty:
            return {
                'error': 'No valid Winner data',
                'winner_distribution': {},
                'most_common_winner': None,
                'consistency_rate': 0.0,
                'entropy': 0.0,
                'max_entropy': 0.0
            }

        winners = valid_df.groupby('Run')['Winner'].first()
        winner_counts = winners.value_counts().sort_index()

        most_common_winner = winner_counts.idxmax()
        most_common_count = winner_counts.max()
        total_runs = len(winners)
        consistency_rate = most_common_count / total_runs * 100

        # Calculate entropy (measures uncertainty)
        probs = winner_counts / total_runs
        entropy = -np.sum(probs * np.log2(probs))

        # Convert formula numbers to integers (avoid float types, e.g., 5.0 -> 5)
        winner_distribution = {int(k): int(v) for k, v in winner_counts.to_dict().items()}

        return {
            'winner_distribution': winner_distribution,
            'most_common_winner': int(most_common_winner),
            'most_common_count': int(most_common_count),
            'total_runs': int(total_runs),
            'consistency_rate': consistency_rate,
            'entropy': entropy,
            'max_entropy': np.log2(len(winner_counts)) if len(winner_counts) > 0 else 0
        }

    def analyze_all_models(self) -> None:
        """
        Analyze reliability of all models

        For each loaded model, perform the following analyses:
        1. Scoring consistency analysis (calculate CV, standard deviation, etc.)
        2. Intraclass Correlation Coefficient (ICC) analysis
        3. Winner formula consistency analysis

        Results are stored in self.analysis_results dictionary
        """
        print("\n" + "=" * 80)
        print("Step 2: Calculating reliability metrics")
        print("=" * 80)

        for model, df in self.all_data.items():
            print(f"\n{'=' * 80}")
            print(f"Analyzing model: {model}")
            print(f"{'=' * 80}")

            self.analysis_results[model] = {}

            # 1. Calculate scoring reliability
            print("\n[Scoring Consistency Analysis]")
            metrics = self.calculate_reliability_metrics(df)
            self.analysis_results[model]['scoring_reliability'] = metrics

            for criterion, stats in metrics.items():
                print(f"\n{criterion}:")
                print(f"  Average CV: {stats['overall_cv']:.2f}%")
                print(f"  Maximum CV: {stats['max_cv']:.2f}%")
                print(f"  Minimum CV: {stats['min_cv']:.2f}%")
                print(f"  Consistency Ratio: {stats['consistency_ratio']:.3f}")

            # 2. Calculate ICC
            print("\n[Intraclass Correlation Coefficient (ICC) Analysis]")
            self.analysis_results[model]['icc_scores'] = {}

            for criterion in self.criteria:
                icc = self.calculate_icc(df, criterion)
                if icc is not None:
                    self.analysis_results[model]['icc_scores'][criterion] = icc
                    print(f"  {criterion}: {icc:.4f}")

            # 3. Analyze winner formula consistency
            print("\n[Winner Formula Consistency Analysis]")
            winner_analysis = self.analyze_winner_consistency(df)
            self.analysis_results[model]['winner_consistency'] = winner_analysis

            if 'error' not in winner_analysis:
                print(f"  Total runs: {winner_analysis['total_runs']}")
                print(f"  Most common winner: Formula {winner_analysis['most_common_winner']}")
                print(f"  Occurrence count: {winner_analysis['most_common_count']}")
                print(f"  Consistency rate: {winner_analysis['consistency_rate']:.1f}%")
                print(f"  Entropy: {winner_analysis['entropy']:.3f} / {winner_analysis['max_entropy']:.3f}")
            else:
                print(f"  Error: {winner_analysis['error']}")

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary report

        Summarizes reliability metrics for all models, generates comparison tables and assessment conclusions

        Returns:
            Dictionary containing summary data
        """
        print("\n" + "=" * 80)
        print("Step 3: Generating summary report")
        print("=" * 80)

        summary = {
            'models_analyzed': list(self.all_data.keys()),
            'overall_findings': {}
        }

        for model in self.all_data.keys():
            if model not in self.analysis_results:
                continue

            results = self.analysis_results[model]

            # Calculate overall reliability score
            reliability_scores = []

            # Scoring consistency (lower CV is better)
            scoring_reliability = results['scoring_reliability']
            avg_cv = np.mean([s['overall_cv'] for s in scoring_reliability.values()])
            reliability_scores.append(('Scoring_CV', avg_cv))

            # ICC score (higher is better)
            icc_scores = [s for s in results['icc_scores'].values() if not np.isnan(s)]
            if icc_scores:
                avg_icc = np.mean(icc_scores)
                reliability_scores.append(('ICC', avg_icc))

            # Winner consistency (higher is better)
            winner_consistency = results['winner_consistency']
            if 'error' not in winner_consistency:
                consistency_rate = winner_consistency['consistency_rate']
                reliability_scores.append(('Winner_Consistency', consistency_rate))

            summary['overall_findings'][model] = reliability_scores

        # Print summary table
        print("\n[Model Reliability Comparison]")
        print("-" * 80)
        print(f"{'Model':<35} {'Avg CV(%)':<12} {'Avg ICC':<12} {'Winner Consistency(%)':<15}")
        print("-" * 80)

        for model, scores in summary['overall_findings'].items():
            score_dict = dict(scores)
            cv = score_dict.get('Scoring_CV', 'N/A')
            icc = score_dict.get('ICC', 'N/A')
            winner = score_dict.get('Winner_Consistency', 'N/A')

            if cv != 'N/A':
                cv_str = f"{cv:.2f}"
            else:
                cv_str = "N/A"

            if icc != 'N/A':
                icc_str = f"{icc:.4f}"
            else:
                icc_str = "N/A"

            if winner != 'N/A':
                winner_str = f"{winner:.1f}%"
            else:
                winner_str = "N/A"

            print(f"{model:<35} {cv_str:<12} {icc_str:<12} {winner_str:<15}")

        print("-" * 80)

        # Generate conclusions
        print("\n[Statistical Reliability Conclusions]")
        print("=" * 80)

        for model, scores in summary['overall_findings'].items():
            score_dict = dict(scores)

            cv = score_dict.get('Scoring_CV')
            icc = score_dict.get('ICC')
            winner = score_dict.get('Winner_Consistency')

            print(f"\n{model}:")
            print("-" * 40)

            reliability_verdict = []

            if cv is not None:
                if cv < 10:
                    reliability_verdict.append("✓ Excellent scoring consistency (CV < 10%)")
                elif cv < 20:
                    reliability_verdict.append("✓ Good scoring consistency (10% ≤ CV < 20%)")
                else:
                    reliability_verdict.append("△ Fair scoring consistency (CV ≥ 20%)")

            if icc is not None:
                if icc > 0.8:
                    reliability_verdict.append("✓ Excellent intra-rater consistency (ICC > 0.8)")
                elif icc > 0.6:
                    reliability_verdict.append("✓ Good intra-rater consistency (0.6 < ICC ≤ 0.8)")
                else:
                    reliability_verdict.append("△ Fair intra-rater consistency (ICC ≤ 0.6)")

            if winner is not None:
                if winner > 80:
                    reliability_verdict.append("✓ Excellent decision consistency (≥ 80%)")
                elif winner > 60:
                    reliability_verdict.append("✓ Good decision consistency (60% - 80%)")
                else:
                    reliability_verdict.append("△ Fair decision consistency (< 60%)")

            for verdict in reliability_verdict:
                print(f"  {verdict}")

            # Overall assessment
            excellent_count = sum(1 for v in reliability_verdict if "✓" in v and "Excellent" in v)
            good_count = sum(1 for v in reliability_verdict if "✓" in v and "Good" in v)

            if excellent_count >= 2:
                overall = "✓✓✓ High statistical reliability"
            elif excellent_count + good_count >= 2:
                overall = "✓✓ Good statistical reliability"
            elif excellent_count + good_count >= 1:
                overall = "✓ Moderate statistical reliability"
            else:
                overall = "△ Low statistical reliability"

            print(f"\n  Overall Assessment: {overall}")

        print("\n" + "=" * 80)
        print("Analysis complete!")
        print("=" * 80)

        return summary

    def export_results(self, output_file: str = "reliability_analysis_results.json") -> None:
        """
        Export analysis results to JSON file

        Exports all analysis results from self.analysis_results to JSON format,
        facilitating subsequent analysis and report generation

        Args:
            output_file: Output filename, defaults to "reliability_analysis_results.json"
        """
        export_data = {}

        for model, results in self.analysis_results.items():
            export_data[model] = {}

            # Convert scoring_reliability
            if 'scoring_reliability' in results:
                export_data[model]['scoring_reliability'] = {}
                for criterion, stats in results['scoring_reliability'].items():
                    export_data[model]['scoring_reliability'][criterion] = {
                        'overall_cv': float(stats['overall_cv']),
                        'overall_std': float(stats['overall_std']),
                        'max_cv': float(stats['max_cv']),
                        'min_cv': float(stats['min_cv']),
                        'consistency_ratio': float(stats['consistency_ratio'])
                    }

            # Convert ICC scores
            if 'icc_scores' in results:
                export_data[model]['icc_scores'] = {
                    k: float(v) for k, v in results['icc_scores'].items()
                }

            # Convert winner_consistency
            if 'winner_consistency' in results:
                wc = results['winner_consistency']
                if 'error' not in wc:
                    export_data[model]['winner_consistency'] = {
                        'winner_distribution': wc['winner_distribution'],
                        'most_common_winner': int(wc['most_common_winner']),
                        'most_common_count': int(wc['most_common_count']),
                        'total_runs': int(wc['total_runs']),
                        'consistency_rate': float(wc['consistency_rate']),
                        'entropy': float(wc['entropy']),
                        'max_entropy': float(wc['max_entropy'])
                    }
                else:
                    export_data[model]['winner_consistency'] = wc

        output_path = self.base_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\nResults exported to: {output_path}")


def main():
    """
    Main function

    Executes complete LLM reliability analysis workflow:
    1. Initialize analyzer
    2. Load all model data
    3. Calculate reliability metrics
    4. Generate summary report
    5. Export analysis results
    """
    print("LLM Multi-Run Reliability Analysis")
    print("=" * 80)

    # Create analyzer instance
    analyzer = LLMReliabilityAnalyzer()

    # Step 1: Load data
    try:
        analyzer.load_all_data()
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nPlease run extract_data.py first to extract data!")
        return

    # Check if data was successfully loaded
    if not analyzer.all_data:
        print("\nError: Failed to load any data")
        return

    # Step 2: Analyze all models
    analyzer.analyze_all_models()

    # Step 3: Generate summary report
    analyzer.generate_summary_report()

    # Step 4: Export results
    analyzer.export_results()


if __name__ == "__main__":
    main()
