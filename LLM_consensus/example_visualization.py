"""
Example: Using the Visualization Package

This script demonstrates how to use the modular visualization functions
to generate LLM reliability analysis charts.
"""

# Method 1: Import all functions
from visualization import *

# Method 2: Import specific functions
# from visualization import (
#     load_analysis_data,
#     plot_overall_comparison,
#     plot_cv_comparison,
#     plot_icc_comparison,
#     plot_winner_consistency,
#     plot_reliability_ranking,
#     plot_entropy_analysis,
#     plot_model_detail
# )

# Method 3: Import the package
# import visualization
# data = visualization.load_analysis_data()
# visualization.plot_overall_comparison(data)


def generate_all_charts():
    """Generate all visualization charts"""
    print("=" * 80)
    print("LLM Reliability Analysis - Visualization Example")
    print("=" * 80)

    # Load analysis data
    try:
        data = load_analysis_data()
        print("\n[OK] Successfully loaded analysis data")
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("Please run analyze_llm_reliability.py first to generate analysis results")
        return

    print("\nGenerating visualization charts...")
    print("-" * 80)

    # 1. Overall comparison radar chart
    print("\n1. Generating overall comparison radar chart...")
    plot_overall_comparison(data, base_dir=".", save=True, show=False)

    # 2. CV comparison bar chart
    print("\n2. Generating CV comparison bar chart...")
    plot_cv_comparison(data, base_dir=".", save=True, show=False)

    # 3. ICC heatmap
    print("\n3. Generating ICC heatmap...")
    plot_icc_comparison(data, base_dir=".", save=True, show=False)

    # 4. Winner consistency chart
    print("\n4. Generating winner consistency chart...")
    plot_winner_consistency(data, base_dir=".", save=True, show=False)

    # 5. Reliability ranking chart
    print("\n5. Generating reliability ranking chart...")
    plot_reliability_ranking(data, base_dir=".", save=True, show=False)

    # 6. Entropy analysis chart
    print("\n6. Generating entropy analysis chart...")
    plot_entropy_analysis(data, base_dir=".", save=True, show=False)

    # 7. Detailed analysis for each model
    print("\n7. Generating detailed analysis charts for each model...")
    models = list(data.keys())
    for model in models:
        print(f"   - {model}")
        plot_model_detail(data, model, base_dir=".", save=True, show=False)

    print("-" * 80)
    print(f"\n[OK] All charts generated successfully!")
    print(f"[OK] Save location: visualizations/")


def generate_specific_charts():
    """Generate specific charts - customize as needed"""
    print("=" * 80)
    print("Generating Specific Charts Only")
    print("=" * 80)

    # Load data
    data = load_analysis_data()

    # Example: Generate only the overall comparison and ICC heatmap
    print("\nGenerating overall comparison and ICC heatmap...")
    plot_overall_comparison(data, base_dir=".", save=True, show=False)
    plot_icc_comparison(data, base_dir=".", save=True, show=False)

    # Example: Generate detailed analysis for a specific model
    print("\nGenerating detailed analysis for GPT-5...")
    plot_model_detail(data, 'gpt-5', base_dir=".", save=True, show=False)

    print("\n[OK] Selected charts generated!")


def generate_with_display():
    """Generate charts and display them interactively"""
    print("=" * 80)
    print("Generating Charts with Display")
    print("=" * 80)

    # Load data
    data = load_analysis_data()

    # Generate and show a single chart
    print("\nGenerating and displaying overall comparison...")
    plot_overall_comparison(data, base_dir=".", save=True, show=True)

    print("\n[OK] Chart displayed!")




def main():
    """Main function for pipeline integration"""
    generate_all_charts()

if __name__ == "__main__":
# Example 2: Generate specific charts only
# generate_specific_charts()

# Example 3: Generate with display (requires GUI environment)
# generate_with_display()
    generate_all_charts()

    # generate_specific_charts()



def main():
    """Main function for pipeline integration"""
    generate_all_charts()


if __name__ == "__main__":
    main()
