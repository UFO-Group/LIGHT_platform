"""
LLM Reliability Analysis Visualization Package

This package provides modular visualization functions for LLM reliability analysis results.
Each module can be used independently to generate specific charts.

Usage Examples:
    # Import all visualization functions
    from visualization import *

    # Load data
    data = load_analysis_data()

    # Generate specific visualizations
    plot_overall_comparison(data)
    plot_cv_comparison(data)
    plot_icc_comparison(data)

    # Or import specific functions
    from visualization import plot_overall_comparison, plot_cv_comparison
    from visualization import load_analysis_data

    data = load_analysis_data()
    plot_overall_comparison(data, base_dir=".", save=True, show=False)
"""

# Import utility functions
from .visualize_utils import (
    load_analysis_data,
    get_output_dir,
    MODEL_COLORS,
    MODEL_NAMES,
    CRITERION_NAMES
)

# Import all visualization functions
from .visualize_comparison import plot_overall_comparison
from .visualize_cv import plot_cv_comparison
from .visualize_icc import plot_icc_comparison
from .visualize_consistency import plot_winner_consistency
from .visualize_ranking import plot_reliability_ranking
from .visualize_entropy import plot_entropy_analysis
from .visualize_model_detail import plot_model_detail

# Define what gets imported with "from visualization import *"
__all__ = [
    # Utility functions
    'load_analysis_data',
    'get_output_dir',
    'MODEL_COLORS',
    'MODEL_NAMES',
    'CRITERION_NAMES',

    # Visualization functions
    'plot_overall_comparison',
    'plot_cv_comparison',
    'plot_icc_comparison',
    'plot_winner_consistency',
    'plot_reliability_ranking',
    'plot_entropy_analysis',
    'plot_model_detail',
]

__version__ = '1.0.0'
