"""
Popularity bias analysis execution script

One-click run complete workflow:
1. Fetch material frequencies (Datamuse + ArXiv)
2. Calculate formula relative frequencies (halo effect)
3. Analyze Spearman correlation (each model independently)
4. Debiasing (each model independently)
5. Generate visualizations

Key principle: Each model analyzed completely independently
"""

import sys
import os

# Set UTF-8 encoding (Windows compatible)
sys.stdout.reconfigure(encoding='utf-8')

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main function"""
    print("=" * 80)
    print("Popularity bias analysis - execution script")
    print("=" * 80)
    print()

    # Step 1: Analysis
    print("[Step 1/2] Running popularity bias analysis...")
    print("-" * 80)
    from analysis.analyze_popularity_bias import PopularityBiasAnalyzer
    analyzer = PopularityBiasAnalyzer()
    analysis_results = analyzer.run_full_analysis()
    print()

    # Step 2: Visualization
    print("[Step 2/2] Generating visualizations...")
    print("-" * 80)
    from visualization.visualize_popularity_bias import PopularityBiasVisualizer
    visualizer = PopularityBiasVisualizer()

    # Get model list
    models = list(analysis_results.keys())

    # Generate visualizations
    visualizer.generate_all_visualizations(models)

    # Create summary report
    visualizer.create_summary_report(models)

    print()
    print("=" * 80)
    print("✓ Analysis complete!")
    print(f"✓ Results saved to: analysis/popularity_bias_analysis/")
    print(f"✓ Visualizations saved to: analysis/popularity_bias_analysis/visualization/")
    print("=" * 80)


if __name__ == "__main__":
    main()
