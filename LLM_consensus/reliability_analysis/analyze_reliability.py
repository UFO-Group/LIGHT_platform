"""
LLM Consensus Reliability Analysis
Analyze the scoring reliability of multiple runs of the same AI model
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
import sys
import io


class LLMReliabilityAnalyzer:
    """Analyze the reliability of multiple LLM runs"""

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
        self.all_data = {}  # Raw data for all models
        self.analysis_results = {}  # Analysis results

    def load_data_from_json(self, json_file: str) -> Dict[str, pd.DataFrame]:
        """
        Load previously extracted data from a JSON file

        Args:
            json_file: path to the JSON file

        Returns:
            Dict mapping model name to DataFrame
        """
        file_path = self.base_dir / json_file

        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")

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

        Loads data from a previously extracted JSON file
        """
        print("=" * 80)
        print("步骤 1: 加载数据")
        print("=" * 80)

        self.all_data = self.load_data_from_json(self.data_file)

        for model, df in self.all_data.items():
            print(f"\n{model}:")
            print(f"  ✓ 成功加载 {len(df)} 条记录，{df['Run'].nunique()} 轮运行")

            # Check the Winner field
            if 'Winner' in df.columns:
                winner_counts = df[df['Winner'].notna()].groupby('Run')['Winner'].first()
                print(f"  - 提取到 {len(winner_counts)} 个获胜配方")
            else:
                print(f"  ⚠ 警告: 缺少Winner列")

        print(f"\n总共加载了 {len(self.all_data)} 个模型的数据")

    def calculate_reliability_metrics(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Compute reliability metrics

        For each criterion the following metrics are computed:
        - Coefficient of variation (CV): std / mean × 100%
        - Standard deviation (Std)
        - Range
        - Consistency ratio

        Args:
            df: DataFrame with multi-run data

        Returns:
            Dict mapping criterion name to a dict of statistical metrics
        """
        results = {}

        # Group by run and formula
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

            # Compute per-formula statistics across all runs
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

                # Compute overall reliability metrics
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
        Compute the intraclass correlation coefficient (ICC) - assesses
        inter-rater agreement

        Based on Shrout & Fleiss (1979):
        - ICC(1,1): one-way random effects model, single measurement
        - ICC(2,1): two-way random effects model, single measurement, consistency
        - ICC(3,1): two-way fixed effects model, single measurement, absolute agreement
        - ICC(3,k): two-way fixed effects model, average measurement, absolute agreement

        Args:
            df: DataFrame with multi-run data
            criterion: criterion to analyze
            icc_type: ICC type, default 'ICC3' (two-way fixed effects, absolute agreement)

        Returns:
            ICC value in [-1, 1]; values closer to 1 mean better agreement
            None: not enough data to compute
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
        n_raters = data_matrix.shape[0]  # number of raters (runs)
        n_targets = data_matrix.shape[1]  # number of targets (formulas)

        # Compute ICC via two-way ANOVA
        return self._calculate_icc_anova(data_matrix, icc_type)

    def _calculate_icc_anova(
        self,
        data_matrix: np.ndarray,
        icc_type: str = 'ICC3'
    ) -> Optional[float]:
        """
        Compute ICC using the ANOVA method

        Args:
            data_matrix: score matrix of shape (n_raters, n_targets)
            icc_type: ICC type

        Returns:
            ICC value, or None if the computation fails
        """
        if data_matrix.size == 0:
            return None

        n_raters = data_matrix.shape[0]
        n_targets = data_matrix.shape[1]

        # Compute the grand mean
        grand_mean = np.mean(data_matrix)

        # Compute the between-targets sum of squares
        target_means = np.mean(data_matrix, axis=0)
        ss_between_targets = n_raters * np.sum((target_means - grand_mean) ** 2)
        df_between_targets = n_targets - 1

        # Compute the between-raters sum of squares
        rater_means = np.mean(data_matrix, axis=1)
        ss_between_raters = n_targets * np.sum((rater_means - grand_mean) ** 2)
        df_between_raters = n_raters - 1

        # Compute the total sum of squares
        ss_total = np.sum((data_matrix - grand_mean) ** 2)

        # Compute the error sum of squares (residual)
        ss_error = ss_total - ss_between_targets - ss_between_raters
        df_error = (n_targets - 1) * (n_raters - 1)

        # Compute mean squares
        ms_between_targets = ss_between_targets / df_between_targets if df_between_targets > 0 else 0
        ms_between_raters = ss_between_raters / df_between_raters if df_between_raters > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0

        # Compute ICC following the formulas of Shrout & Fleiss (1979)
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

        # The ICC should theoretically lie in [-1, 1]
        # Numerical error can push it outside; clamp it
        icc = max(min(icc, 1.0), -1.0)

        return icc

    def analyze_winner_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the consistency of winning formulas

        Computes the following metrics:
        - Winning formula distribution
        - Most common winning formula
        - Consistency rate (frequency of the most common winning formula)
        - Entropy (uncertainty of the winning formula)
        - Max entropy (entropy if all formulas were equally likely)

        Args:
            df: DataFrame containing a Winner column

        Returns:
            Dict with the consistency analysis results
        """
        if 'Winner' not in df.columns:
            return {
                'error': '缺少Winner列',
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
                'error': '没有有效的Winner数据',
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

        # Compute entropy (measures uncertainty)
        probs = winner_counts / total_runs
        entropy = -np.sum(probs * np.log2(probs))

        # Convert formula numbers to ints (avoid float type, e.g. 5.0 -> 5)
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

    def analyze_winner_margin(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the score gap between the best and runner-up formulas
        (Winner Margin)

        Assesses cascading divergence risk:
        - If the best and runner-up scores are very close, the optimal choice
          is easily affected by small fluctuations
        - Computes the top-1 vs top-2 score gap for each run
        - Analyzes the distribution of these gaps statistically

        Args:
            df: DataFrame with multi-run data

        Returns:
            Dict with the margin analysis results
        """
        if 'Total_Score' not in df.columns:
            return {
                'error': '缺少Total_Score列',
                'avg_margin': 0.0,
                'std_margin': 0.0,
                'cv_margin': 0.0,
                'min_margin': 0.0,
                'max_margin': 0.0,
                'margin_distribution': {},
                'cascading_risk': '',
                'risk_level': 'Unknown'
            }

        margins = []

        # Group by run and compute the top-1 vs top-2 score gap per run
        for run_num in df['Run'].unique():
            run_df = df[df['Run'] == run_num].copy()

            # Sort by Total_Score descending
            run_df = run_df.sort_values('Total_Score', ascending=False)

            if len(run_df) >= 2:
                # Get the top-1 and top-2 scores
                first_score = run_df.iloc[0]['Total_Score']
                second_score = run_df.iloc[1]['Total_Score']

                # Compute the score gap
                margin = first_score - second_score
                margins.append(margin)

        if not margins:
            return {
                'error': '无法计算margin（数据不足）',
                'avg_margin': 0.0,
                'std_margin': 0.0,
                'cv_margin': 0.0,
                'min_margin': 0.0,
                'max_margin': 0.0,
                'margin_distribution': {},
                'cascading_risk': '',
                'risk_level': 'Unknown'
            }

        margins = np.array(margins)

        # Statistical analysis
        avg_margin = np.mean(margins)
        std_margin = np.std(margins, ddof=1) if len(margins) > 1 else 0.0
        cv_margin = (std_margin / avg_margin * 100) if avg_margin > 0 else 0.0
        min_margin = np.min(margins)
        max_margin = np.max(margins)

        # Assess cascading divergence risk
        # Risk level is based on the average margin and the minimum margin
        if avg_margin < 1.0:
            risk_level = "高风险"
            risk = (f"最优与次优得分差异极小（平均{avg_margin:.2f}分），"
                    f"决策极易受到cascading divergence影响。"
                    f"微小的评分波动可能导致最优选择改变，建议增加一致性。")
        elif avg_margin < 2.0:
            risk_level = "中风险"
            risk = (f"最优与次优得分差异较小（平均{avg_margin:.2f}分），"
                    f"存在一定的cascading divergence风险。"
                    f"在某些run中，评分波动可能改变最优选择。")
        elif avg_margin < 3.0:
            risk_level = "低风险"
            risk = (f"最优与次优得分差异适中（平均{avg_margin:.2f}分），"
                    f"cascading divergence风险较低。"
                    f"最优选择相对稳定，但仍有改进空间。")
        else:
            risk_level = "极低风险"
            risk = (f"最优与次优得分差异明显（平均{avg_margin:.2f}分），"
                    f"cascading divergence风险极低。"
                    f"最优选择非常稳定，决策一致性高。")

        # Warn if the minimum margin is very small, even when the average
        # margin is large
        if min_margin < 1.0 and risk_level != "高风险":
            risk += f" 注意：存在margin小于1.0的run（最小{min_margin:.2f}），这些run可能不稳定。"

        return {
            'avg_margin': float(avg_margin),
            'std_margin': float(std_margin),
            'cv_margin': float(cv_margin),
            'min_margin': float(min_margin),
            'max_margin': float(max_margin),
            'margin_count': len(margins),
            'cascading_risk': risk,
            'risk_level': risk_level
        }

    def analyze_all_models(self) -> None:
        """
        Analyze the reliability of all models

        For each loaded model the following analyses are run:
        1. Scoring consistency analysis (CV, standard deviation, etc.)
        2. Intraclass correlation coefficient (ICC) analysis
        3. Winning formula consistency analysis
        4. Best vs runner-up gap analysis (cascading divergence risk)

        Results are stored in the self.analysis_results dict
        """
        print("\n" + "=" * 80)
        print("步骤 2: 计算可靠性指标")
        print("=" * 80)

        for model, df in self.all_data.items():
            print(f"\n{'=' * 80}")
            print(f"分析模型: {model}")
            print(f"{'=' * 80}")

            self.analysis_results[model] = {}

            # 1. Compute scoring reliability
            print("\n【评分一致性分析】")
            metrics = self.calculate_reliability_metrics(df)
            self.analysis_results[model]['scoring_reliability'] = metrics

            for criterion, stats in metrics.items():
                print(f"\n{criterion}:")
                print(f"  平均变异系数 (CV): {stats['overall_cv']:.2f}%")
                print(f"  最大变异系数: {stats['max_cv']:.2f}%")
                print(f"  最小变异系数: {stats['min_cv']:.2f}%")
                print(f"  一致性比率: {stats['consistency_ratio']:.3f}")

            # 2. Compute ICC
            print("\n【组内相关系数 (ICC) 分析】")
            self.analysis_results[model]['icc_scores'] = {}

            for criterion in self.criteria:
                icc = self.calculate_icc(df, criterion)
                if icc is not None:
                    self.analysis_results[model]['icc_scores'][criterion] = icc
                    print(f"  {criterion}: {icc:.4f}")

            # 3. Analyze winning formula consistency
            print("\n【获胜配方一致性分析】")
            winner_analysis = self.analyze_winner_consistency(df)
            self.analysis_results[model]['winner_consistency'] = winner_analysis

            if 'error' not in winner_analysis:
                print(f"  总运行轮数: {winner_analysis['total_runs']}")
                print(f"  最常见获胜配方: Formula {winner_analysis['most_common_winner']}")
                print(f"  出现次数: {winner_analysis['most_common_count']}")
                print(f"  一致性率: {winner_analysis['consistency_rate']:.1f}%")
                print(f"  熵: {winner_analysis['entropy']:.3f} / {winner_analysis['max_entropy']:.3f}")
            else:
                print(f"  错误: {winner_analysis['error']}")

            # 4. Analyze the best vs runner-up gap
            print("\n【最优-次优配方差异分析】")
            margin_analysis = self.analyze_winner_margin(df)
            self.analysis_results[model]['winner_margin'] = margin_analysis

            if 'error' not in margin_analysis:
                print(f"  平均得分差: {margin_analysis['avg_margin']:.2f}")
                print(f"  得分差标准差: {margin_analysis['std_margin']:.2f}")
                print(f"  得分差变异系数: {margin_analysis['cv_margin']:.2f}%")
                print(f"  最小得分差: {margin_analysis['min_margin']:.2f}")
                print(f"  最大得分差: {margin_analysis['max_margin']:.2f}")

                # Assess cascading divergence risk
                risk = margin_analysis['cascading_risk']
                risk_level = margin_analysis['risk_level']
                print(f"  Cascading Divergence风险: {risk_level}")
                print(f"  评估: {risk}")
            else:
                print(f"  错误: {margin_analysis['error']}")

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report

        Aggregates reliability metrics across models, producing comparison
        tables and assessment verdicts

        Returns:
            Dict with summary data
        """
        print("\n" + "=" * 80)
        print("步骤 3: 生成总结报告")
        print("=" * 80)

        summary = {
            'models_analyzed': list(self.all_data.keys()),
            'overall_findings': {}
        }

        for model in self.all_data.keys():
            if model not in self.analysis_results:
                continue

            results = self.analysis_results[model]

            # Compute overall reliability scores
            reliability_scores = []

            # Scoring consistency (lower CV is better)
            scoring_reliability = results['scoring_reliability']
            avg_cv = np.mean([s['overall_cv'] for s in scoring_reliability.values()])
            reliability_scores.append(('Scoring_CV', avg_cv))

            # ICC scores (higher is better)
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

        # Print the summary table
        print("\n【各模型可靠性对比】")
        print("-" * 80)
        print(f"{'模型':<35} {'平均CV(%)':<12} {'平均ICC':<12} {'获胜一致性(%)':<15}")
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

        # Generate verdicts
        print("\n【统计可靠性结论】")
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
                    reliability_verdict.append("✓ 评分一致性优秀 (CV < 10%)")
                elif cv < 20:
                    reliability_verdict.append("✓ 评分一致性良好 (10% ≤ CV < 20%)")
                else:
                    reliability_verdict.append("△ 评分一致性一般 (CV ≥ 20%)")

            if icc is not None:
                if icc > 0.8:
                    reliability_verdict.append("✓ 组内一致性优秀 (ICC > 0.8)")
                elif icc > 0.6:
                    reliability_verdict.append("✓ 组内一致性良好 (0.6 < ICC ≤ 0.8)")
                else:
                    reliability_verdict.append("△ 组内一致性一般 (ICC ≤ 0.6)")

            if winner is not None:
                if winner > 80:
                    reliability_verdict.append("✓ 决策一致性优秀 (≥ 80%)")
                elif winner > 60:
                    reliability_verdict.append("✓ 决策一致性良好 (60% - 80%)")
                else:
                    reliability_verdict.append("△ 决策一致性一般 (< 60%)")

            for verdict in reliability_verdict:
                print(f"  {verdict}")

            # Overall assessment
            excellent_count = sum(1 for v in reliability_verdict if "✓" in v and "优秀" in v)
            good_count = sum(1 for v in reliability_verdict if "✓" in v and "良好" in v)

            if excellent_count >= 2:
                overall = "✓✓✓ 统计可靠性高"
            elif excellent_count + good_count >= 2:
                overall = "✓✓ 统计可靠性较高"
            elif excellent_count + good_count >= 1:
                overall = "✓ 统计可靠性中等"
            else:
                overall = "△ 统计可靠性较低"

            print(f"\n  总体评估: {overall}")

        print("\n" + "=" * 80)
        print("分析完成！")
        print("=" * 80)

        return summary

    def export_results(self, output_file: str = "reliability_analysis_results.json") -> None:
        """
        Export analysis results to a JSON file

        Exports all analysis results from self.analysis_results as JSON for
        downstream analysis and report generation

        Args:
            output_file: output file name, defaults to
                "reliability_analysis_results.json"
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

            # Convert winner_margin
            if 'winner_margin' in results:
                wm = results['winner_margin']
                if 'error' not in wm:
                    export_data[model]['winner_margin'] = {
                        'avg_margin': float(wm['avg_margin']),
                        'std_margin': float(wm['std_margin']),
                        'cv_margin': float(wm['cv_margin']),
                        'min_margin': float(wm['min_margin']),
                        'max_margin': float(wm['max_margin']),
                        'margin_count': int(wm['margin_count']),
                        'cascading_risk': wm['cascading_risk'],
                        'risk_level': wm['risk_level']
                    }
                else:
                    export_data[model]['winner_margin'] = wm

        output_path = self.base_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\n结果已导出到: {output_path}")


def main():
    """
    Main function

    Runs the full LLM reliability analysis pipeline:
    1. Initialize the analyzer
    2. Load data for all models
    3. Compute reliability metrics
    4. Generate the summary report
    5. Export the analysis results
    """
    # Set UTF-8 encoding (Windows)
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("LLM 多轮运行可靠性分析")
    print("=" * 80)

    # Create the analyzer instance
    analyzer = LLMReliabilityAnalyzer()

    # Step 1: load data
    try:
        analyzer.load_all_data()
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("\n请先运行 extract_data.py 提取数据！")
        return

    # Check whether any data was loaded
    if not analyzer.all_data:
        print("\n错误: 未能加载任何数据")
        return

    # Step 2: analyze all models
    analyzer.analyze_all_models()

    # Step 3: generate the summary report
    analyzer.generate_summary_report()

    # Step 4: export the results
    analyzer.export_results()


if __name__ == "__main__":
    main()
