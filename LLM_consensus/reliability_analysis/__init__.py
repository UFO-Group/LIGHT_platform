"""
Data Analysis Module for LLM Consensus Reliability Analysis

This module provides functionality for:
- Extracting data from markdown files
- Analyzing statistical reliability (CV, ICC, consistency, entropy)

Usage:
    from analysis import extract_data, analyze_reliability

    # Extract data from markdown files
    extract_data.main()

    # Run reliability analysis
    analyze_reliability.main()
"""

from . import extract_data
from . import analyze_reliability

__all__ = ['extract_data', 'analyze_reliability']
