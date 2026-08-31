"""
Popularity Bias Analysis Module

Provides robust regression-based analysis for detecting and correcting
popularity bias in LLM scoring of materials.

Methods:
- Partial Correlation - Control for confounding variables
- Robust Regression - Huber/RANSAC for outlier resistance
"""

from .analysis.robust_regression import RigorousBiasAnalyzer, analyze_popularity_bias

__version__ = "1.0.0"
__all__ = [
    "RigorousBiasAnalyzer",
    "analyze_popularity_bias"
]