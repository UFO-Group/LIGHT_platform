"""
LLM Reliability Analysis Visualization - English Version
Generate various charts to display analysis results
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional
import sys
import io

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set English fonts
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Set seaborn style
sns.set_style("whitegrid")
sns.set_palette("husl")


class LLMResultVisualizer:
    """LLM Reliability Analysis Results Visualization"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.data_file = self.base_dir / "reliability_analysis_results.json"
        self.output_dir = self.base_dir / "visualizations"
        self.output_dir.mkdir(exist_ok=True)

        # Color scheme
        self.model_colors = {
            'gpt-5': '#FF6B6B',
            'grok-4': '#4ECDC4',
            'claude-opus-4-5-20251101': '#45B7D1',
            'gemini-3-pro-preview': '#FFA07A'
        }

        # English model names for display
        self.model_names = {
            'gpt-5': 'GPT-5',
            'grok-4': 'Grok-4',
            'claude-opus-4-5-20251101': 'Claude Opus 4.5',
            'gemini-3-pro-preview': 'Gemini 3 Pro'
        }

    def load_data(self) -> Dict:
        """Load analysis results data"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    def plot_overall_comparison(self, data: Dict, save: bool = True) -> None:
        """Plot overall comparison - Radar chart"""
        # Prepare data
        models = list(data.keys())
        metrics = ['Avg CV', 'Avg ICC', 'Decision Consistency']

        model_scores = {}
        for model in models:
            # Calculate average CV
            avg_cv = np.mean([s['overall_cv'] for s in data[model]['scoring_reliability'].values()])

            # Calculate average ICC
            avg_icc = np.mean(list(data[model]['icc_scores'].values()))

            # Decision consistency
            winner_cons = data[model]['winner_consistency']['consistency_rate']

            model_scores[model] = {
                'Avg CV': 100 - avg_cv,  # Lower CV is better, convert to score
                'Avg ICC': avg_icc * 100,  # Convert ICC to percentage
                'Decision Consistency': winner_cons
            }

        # Create radar chart
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

        # Calculate angles
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]

        # Plot each model
        for model in models:
            values = [model_scores[model][metric] for metric in metrics]
            values += values[:1]

            ax.plot(angles, values, 'o-', linewidth=2,
                   label=model, color=self.model_colors[model])
            ax.fill(angles, values, alpha=0.15, color=self.model_colors[model])

        # Set labels and grid
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=12)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)

        # Title and legend
        plt.title('Comprehensive LLM Model Reliability Comparison\n(Higher values indicate better reliability)',
                 fontsize=14, fontweight='bold', pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'overall_comparison_radar.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: overall_comparison_radar.png")

        plt.close()

    def plot_cv_comparison(self, data: Dict, save: bool = True) -> None:
        """Plot CV comparison bar chart"""
        # Prepare data
        models = list(data.keys())
        criteria = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
                   'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']

        # English criterion names
        criterion_names = {
            'Mechanical_Safety': 'Mechanical Safety',
            'Swelling_Performance': 'Swelling Performance',
            'Endothelialization': 'Endothelialization',
            'SMC_inhibition': 'SMC Inhibition',
            'Anti_inflammation': 'Anti-inflammation',
            'Thrombogenicity': 'Thrombogenicity',
            'Total_Score': 'Total Score'
        }

        cv_data = []
        for model in models:
            for criterion in criteria:
                if criterion in data[model]['scoring_reliability']:
                    cv_data.append({
                        'Model': model,
                        'Criterion': criterion_names[criterion],
                        'CV': data[model]['scoring_reliability'][criterion]['overall_cv']
                    })

        df = pd.DataFrame(cv_data)

        # Create grouped bar chart
        fig, ax = plt.subplots(figsize=(14, 6))

        models_list = list(df['Model'].unique())
        x = np.arange(len(criteria))
        width = 0.2

        for i, model in enumerate(models_list):
            model_data = df[df['Model'] == model]['CV'].values
            ax.bar(x + i * width, model_data, width,
                   label=model, color=self.model_colors[model], alpha=0.8)

        # Add reference lines
        ax.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='Excellent (CV<10%)')
        ax.axhline(y=20, color='orange', linestyle='--', alpha=0.5, label='Fair (CV≥20%)')

        ax.set_xlabel('Scoring Criteria', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coefficient of Variation CV (%)', fontsize=12, fontweight='bold')
        ax.set_title('CV Comparison Across Scoring Criteria\n(Lower is better)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(criterion_names.values(), rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'cv_comparison.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: cv_comparison.png")

        plt.close()

    def plot_icc_comparison(self, data: Dict, save: bool = True) -> None:
        """Plot ICC comparison heatmap"""
        # Prepare data
        models = list(data.keys())
        criteria = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
                   'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']

        # English criterion names
        criterion_names = {
            'Mechanical_Safety': 'Mechanical Safety',
            'Swelling_Performance': 'Swelling Performance',
            'Endothelialization': 'Endothelialization',
            'SMC_inhibition': 'SMC Inhibition',
            'Anti_inflammation': 'Anti-inflammation',
            'Thrombogenicity': 'Thrombogenicity',
            'Total_Score': 'Total Score'
        }

        # Create ICC matrix
        icc_matrix = pd.DataFrame(index=criteria, columns=models)

        for model in models:
            for criterion in criteria:
                if criterion in data[model]['icc_scores']:
                    icc_matrix.loc[criterion, model] = data[model]['icc_scores'][criterion]

        icc_matrix = icc_matrix.astype(float)

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(icc_matrix, annot=True, fmt='.4f', cmap='RdYlGn',
                   vmin=0, vmax=1, cbar_kws={'label': 'ICC Value'},
                   linewidths=0.5, linecolor='white', ax=ax)

        ax.set_title('Intraclass Correlation Coefficient (ICC) Heatmap\n(Higher values indicate better consistency)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Model', fontsize=12, fontweight='bold')
        ax.set_ylabel('Scoring Criteria', fontsize=12, fontweight='bold')

        # Use English criterion names for y-axis
        ax.set_yticklabels([criterion_names.get(c, c) for c in icc_matrix.index])

        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'icc_heatmap.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: icc_heatmap.png")

        plt.close()

    def plot_winner_consistency(self, data: Dict, save: bool = True) -> None:
        """Plot decision consistency comparison"""
        # Prepare data
        models = list(data.keys())

        consistency_data = []
        for model in models:
            wc = data[model]['winner_consistency']
            if 'error' not in wc:
                consistency_data.append({
                    'Model': model,
                    'Consistency Rate (%)': wc['consistency_rate'],
                    'Most Common Winner': f"Formula {int(wc['most_common_winner'])}",
                    'Count': int(wc['most_common_count'])
                })

        df = pd.DataFrame(consistency_data)

        # Create chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Left plot: Consistency rate bar chart
        colors = [self.model_colors[model] for model in df['Model']]
        bars = ax1.bar(df['Model'], df['Consistency Rate (%)'], color=colors, alpha=0.8, edgecolor='black')

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Add reference lines
        ax1.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Excellent (≥80%)')
        ax1.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='Good (≥60%)')

        ax1.set_xlabel('Model', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Decision Consistency Rate (%)', fontsize=12, fontweight='bold')
        ax1.set_title('Decision Consistency Rate Comparison', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim(0, 105)

        # Right plot: Winner distribution stacked bar chart
        all_formulas = set()
        for model in models:
            wc = data[model]['winner_consistency']
            if 'error' not in wc and 'winner_distribution' in wc:
                dist = wc['winner_distribution']
                formulas = sorted(dist.keys())
                all_formulas.update(formulas)
                counts = [dist[f] for f in formulas]

                # Use offset to avoid overlap
                offset = list(models).index(model) * 0.15
                x_pos = np.arange(len(formulas)) + offset

                ax2.bar(x_pos, counts, width=0.15, label=model,
                       color=self.model_colors[model], alpha=0.8)

        ax2.set_xlabel('Winner Formula', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax2.set_title('Winner Formula Distribution', fontsize=12, fontweight='bold')

        if all_formulas:
            formulas_sorted = sorted(all_formulas)
            ax2.set_xticks(np.arange(len(formulas_sorted)) + 0.225)
            ax2.set_xticklabels([f'F{f}' for f in formulas_sorted])
        ax2.legend(fontsize=9, loc='upper right')
        ax2.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'winner_consistency.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: winner_consistency.png")

        plt.close()

    def plot_reliability_ranking(self, data: Dict, save: bool = True) -> None:
        """Plot reliability ranking chart"""
        # Calculate comprehensive scores
        models = list(data.keys())
        scores = []

        for model in models:
            # CV score (lower is better, convert to score)
            avg_cv = np.mean([s['overall_cv'] for s in data[model]['scoring_reliability'].values()])
            cv_score = max(0, 100 - avg_cv * 2)

            # ICC score
            avg_icc = np.mean(list(data[model]['icc_scores'].values()))
            icc_score = avg_icc * 100

            # Decision consistency score
            winner_cons = data[model]['winner_consistency']['consistency_rate']

            # Overall score (weighted average)
            overall_score = cv_score * 0.3 + icc_score * 0.3 + winner_cons * 0.4

            scores.append({
                'Model': model,
                'Scoring Consistency': cv_score,
                'Inter-rater Reliability': icc_score,
                'Decision Stability': winner_cons,
                'Overall Score': overall_score
            })

        df = pd.DataFrame(scores).sort_values('Overall Score', ascending=True)

        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        y_pos = np.arange(len(df))
        colors = [self.model_colors[model] for model in df['Model']]

        ax.barh(y_pos, df['Overall Score'], color=colors, alpha=0.8, edgecolor='black')

        # Add value labels
        for i, (idx, row) in enumerate(df.iterrows()):
            ax.text(row['Overall Score'] + 1, i, f"{row['Overall Score']:.1f}",
                   va='center', fontsize=10, fontweight='bold')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['Model'], fontsize=11)
        ax.set_xlabel('Overall Score', fontsize=12, fontweight='bold')
        ax.set_title('LLM Model Reliability Ranking\n(Based on weighted average of scoring consistency, inter-rater reliability, and decision stability)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlim(0, 100)
        ax.grid(axis='x', alpha=0.3)

        # Add legend
        legend_text = 'Scoring Weights:\n• Scoring Consistency: 30%\n• Inter-rater Reliability: 30%\n• Decision Stability: 40%'
        ax.text(0.98, 0.5, legend_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='center', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'reliability_ranking.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: reliability_ranking.png")

        plt.close()

    def plot_model_detail(self, data: Dict, model_name: str, save: bool = True) -> None:
        """Plot detailed analysis for a single model"""
        if model_name not in data:
            print(f"[ERROR] Model {model_name} does not exist")
            return

        model_data = data[model_name]

        # Create subplots
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

        # 1. CV radar chart
        ax1 = fig.add_subplot(gs[0, 0])
        criteria = list(model_data['scoring_reliability'].keys())

        # English criterion names
        criterion_names = {
            'Mechanical_Safety': 'Mechanical Safety',
            'Swelling_Performance': 'Swelling Performance',
            'Endothelialization': 'Endothelialization',
            'SMC_inhibition': 'SMC Inhibition',
            'Anti_inflammation': 'Anti-inflammation',
            'Thrombogenicity': 'Thrombogenicity',
            'Total_Score': 'Total Score'
        }

        cv_values = [model_data['scoring_reliability'][c]['overall_cv'] for c in criteria]

        angles = np.linspace(0, 2 * np.pi, len(criteria), endpoint=False)
        cv_values = cv_values + [cv_values[0]]
        angles = np.concatenate([angles, [angles[0]]])

        ax1.plot(angles, cv_values, 'o-', linewidth=2, color=self.model_colors[model_name])
        ax1.fill(angles, cv_values, alpha=0.25, color=self.model_colors[model_name])
        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels([criterion_names.get(c, c).replace('_', ' ') for c in criteria], fontsize=8)
        ax1.set_ylim(0, max(cv_values) * 1.1)
        ax1.set_title('Coefficient of Variation', fontweight='bold', fontsize=11)
        ax1.grid(True)

        # 2. ICC bar chart
        ax2 = fig.add_subplot(gs[0, 1])
        icc_criteria = list(model_data['icc_scores'].keys())
        icc_values = [model_data['icc_scores'][c] for c in icc_criteria]

        colors_icc = ['green' if v > 0.8 else 'orange' if v > 0.6 else 'red' for v in icc_values]
        ax2.barh(range(len(icc_criteria)), icc_values, color=colors_icc, alpha=0.7, edgecolor='black')
        ax2.set_yticks(range(len(icc_criteria)))
        ax2.set_yticklabels([criterion_names.get(c, c).replace('_', ' ') for c in icc_criteria], fontsize=8)
        ax2.set_xlabel('ICC Value', fontsize=10)
        ax2.set_title('Intraclass Correlation Coefficient', fontweight='bold', fontsize=11)
        ax2.set_xlim(0, 1)
        ax2.axvline(x=0.8, color='green', linestyle='--', alpha=0.5, label='Excellent')
        ax2.axvline(x=0.6, color='orange', linestyle='--', alpha=0.5, label='Good')
        ax2.legend(fontsize=8)
        ax2.grid(axis='x', alpha=0.3)

        # 3. Winner distribution pie chart
        ax3 = fig.add_subplot(gs[0, 2])
        wc = model_data['winner_consistency']
        if 'error' not in wc and 'winner_distribution' in wc:
            dist = wc['winner_distribution']
            formulas = sorted(dist.keys())
            sizes = [dist[f] for f in formulas]
            labels = [f'Formula {f}' for f in formulas]

            colors_pie = plt.cm.Set3(np.linspace(0, 1, len(formulas)))
            wedges, texts, autotexts = ax3.pie(sizes, labels=labels, autopct='%1.1f%%',
                                             colors=colors_pie, startangle=90)
            ax3.set_title(f'Winner Distribution\n(Consistency: {wc["consistency_rate"]:.1f}%)',
                         fontweight='bold', fontsize=11)

        # 4. CV range box plot
        ax4 = fig.add_subplot(gs[1, :])

        summary_data = []
        for criterion in criteria:
            stats = model_data['scoring_reliability'][criterion]
            summary_data.append({
                'Criterion': criterion_names[criterion],
                'Mean': stats['overall_cv'],
                'Max': stats['max_cv'],
                'Min': stats['min_cv']
            })

        df_summary = pd.DataFrame(summary_data)
        x = np.arange(len(criteria))
        width = 0.25

        ax4.bar(x - width, df_summary['Min'], width, label='Min CV', color='lightblue', alpha=0.7)
        ax4.bar(x, df_summary['Mean'], width, label='Mean CV', color=self.model_colors[model_name], alpha=0.7)
        ax4.bar(x + width, df_summary['Max'], width, label='Max CV', color='lightcoral', alpha=0.7)

        ax4.set_xlabel('Scoring Criteria', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Coefficient of Variation (%)', fontsize=11, fontweight='bold')
        ax4.set_title('Coefficient of Variation Statistics', fontweight='bold', fontsize=12)
        ax4.set_xticks(x)
        ax4.set_xticklabels(df_summary['Criterion'], rotation=45, ha='right')
        ax4.legend(fontsize=10)
        ax4.grid(axis='y', alpha=0.3)

        # Main title
        fig.suptitle(f'{self.model_names[model_name]} - Detailed Reliability Analysis',
                    fontsize=16, fontweight='bold', y=0.995)

        if save:
            plt.savefig(self.output_dir / f'{model_name}_detail.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: {model_name}_detail.png")

        plt.close()

    def plot_entropy_analysis(self, data: Dict, save: bool = True) -> None:
        """Plot entropy analysis chart"""
        models = list(data.keys())

        entropy_data = []
        for model in models:
            wc = data[model]['winner_consistency']
            if 'error' not in wc:
                entropy_data.append({
                    'Model': model,
                    'Actual Entropy': wc['entropy'],
                    'Max Entropy': wc['max_entropy'],
                    'Consistency Rate': wc['consistency_rate']
                })

        df = pd.DataFrame(entropy_data)

        # Create chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Left plot: Entropy value comparison
        x = np.arange(len(df))
        width = 0.35

        bars1 = ax1.bar(x - width/2, df['Actual Entropy'], width, label='Actual Entropy',
                       color='steelblue', alpha=0.8)
        bars2 = ax1.bar(x + width/2, df['Max Entropy'], width, label='Max Entropy',
                       color='lightgray', alpha=0.8)

        ax1.set_xlabel('Model', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Entropy Value', fontsize=12, fontweight='bold')
        ax1.set_title('Information Entropy Comparison\n(Lower values indicate more concentrated decisions)',
                     fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(df['Model'], rotation=45, ha='right')
        ax1.legend(fontsize=10)
        ax1.grid(axis='y', alpha=0.3)

        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=8)

        # Right plot: Consistency vs Entropy scatter plot
        for i, row in df.iterrows():
            ax2.scatter(row['Actual Entropy'], row['Consistency Rate'],
                      s=200, color=self.model_colors[row['Model']],
                      alpha=0.7, edgecolor='black', label=row['Model'])
            ax2.annotate(row['Model'], (row['Actual Entropy'], row['Consistency Rate']),
                       fontsize=9, xytext=(5, 5), textcoords='offset points')

        ax2.set_xlabel('Information Entropy', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Decision Consistency Rate (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Entropy vs Consistency Relationship\n(Lower entropy, higher consistency)',
                     fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # Add trend line
        z = np.polyfit(df['Actual Entropy'], df['Consistency Rate'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(df['Actual Entropy'].min(), df['Actual Entropy'].max(), 100)
        ax2.plot(x_trend, p(x_trend), "r--", alpha=0.5, linewidth=2, label='Trend Line')
        ax2.legend(fontsize=9)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'entropy_analysis.png',
                       dpi=300, bbox_inches='tight')
            print(f"[OK] Saved: entropy_analysis.png")

        plt.close()

    def generate_all_visualizations(self, show: bool = False) -> None:
        """Generate all visualization charts"""
        print("=" * 80)
        print("LLM Reliability Analysis - Visualization Generator")
        print("=" * 80)

        # Load data
        try:
            data = self.load_data()
            print(f"\n[OK] Successfully loaded analysis data")
        except FileNotFoundError as e:
            print(f"\n[ERROR] {e}")
            print("Please run analyze_llm_reliability.py first to generate analysis results")
            return

        print(f"\nStarting to generate visualization charts...")
        print(f"Output directory: {self.output_dir}")
        print("-" * 80)

        # Generate various charts
        self.plot_overall_comparison(data)
        self.plot_cv_comparison(data)
        self.plot_icc_comparison(data)
        self.plot_winner_consistency(data)
        self.plot_reliability_ranking(data)
        self.plot_entropy_analysis(data)

        # Generate detailed charts for each model
        print("-" * 80)
        print("\nGenerating detailed analysis charts for each model:")
        for model in data.keys():
            self.plot_model_detail(data, model)

        print("-" * 80)
        print(f"\n[OK] All charts generated! Total: {len(list(self.output_dir.glob('*.png')))} files")
        print(f"[OK] Save location: {self.output_dir}")

        # Display file statistics
        png_files = list(self.output_dir.glob('*.png'))
        total_size = sum(f.stat().st_size for f in png_files) / 1024  # KB

        print(f"\nFile Statistics:")
        print(f"  File count: {len(png_files)}")
        print(f"  Total size: {total_size:.1f} KB")
        print(f"  Average size: {total_size/len(png_files):.1f} KB")

        print("\n" + "=" * 80)
        print("Visualization Complete!")
        print("=" * 80)

        if show:
            print("\nDisplaying charts...")
            import os
            for img_file in sorted(self.output_dir.glob('*.png')):
                os.startfile(str(img_file))


def main():
    """Main function"""
    visualizer = LLMResultVisualizer()
    visualizer.generate_all_visualizations(show=False)


if __name__ == "__main__":
    main()
