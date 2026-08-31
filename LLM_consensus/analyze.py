#!/usr/bin/env python3
"""
LLM Consensus Analysis Module

Provides a unified interface for running various analyses on LLM consensus data.

Available analyses:
1. Popularity Bias Analysis (Robust Regression)
   - Detects and corrects popularity bias in LLM scoring
   - Methods: Partial Correlation + Robust Regression (Huber + RANSAC)

2. Anti-Formula Analysis
   - Extracts arguments against specific formulas from LLM outputs
   - Useful for understanding weaknesses of specific formulations
"""

import argparse
import sys
from typing import Dict, List

# Import analysis modules
try:
    from popularity_bias import RigorousBiasAnalyzer, analyze_popularity_bias
    POPULARITY_BIAS_AVAILABLE = True
except ImportError:
    POPULARITY_BIAS_AVAILABLE = False
    print("Warning: popularity_bias module not available")

try:
    from anti_analysis import AntiArgumentExtractor, extract_anti_arguments
    ANTI_ANALYSIS_AVAILABLE = True
except ImportError:
    ANTI_ANALYSIS_AVAILABLE = False
    print("Warning: anti_analysis module not available")


class AnalysisPipeline:
    """Unified pipeline for running multiple analyses."""

    def __init__(self, project_root: str = None):
        """
        Initialize the analysis pipeline.

        Args:
            project_root: Root directory of the project (default: auto-detect)
        """
        self.project_root = project_root
        self.results = {}

    def run_popularity_bias_analysis(
        self,
        data_dir: str = None,
        results_dir: str = None,
        configure_logging: bool = True
    ) -> Dict:
        """
        Run popularity bias analysis using robust regression.

        Args:
            data_dir: Directory containing input data
            results_dir: Directory for output results
            configure_logging: Whether to configure logging

        Returns:
            Dictionary containing analysis results
        """
        if not POPULARITY_BIAS_AVAILABLE:
            raise RuntimeError("Popularity bias analysis not available")

        print("=" * 80)
        print("Running Popularity Bias Analysis (Robust Regression)")
        print("=" * 80)

        results = analyze_popularity_bias(
            project_root=self.project_root,
            data_dir=data_dir,
            results_dir=results_dir,
            configure_logging=configure_logging
        )

        self.results['popularity_bias'] = results
        return results

    def run_anti_formula_analysis(
        self,
        model_files: Dict[str, str] = None,
        output_dir: str = None,
        formulas: List[int] = None
    ) -> Dict[int, List[str]]:
        """
        Run anti-formula analysis to extract arguments against specific formulas.

        Args:
            model_files: Dictionary mapping model names to their output files
            output_dir: Directory for output results
            formulas: List of formula numbers to extract arguments for

        Returns:
            Dictionary mapping formula numbers to lists of arguments
        """
        if not ANTI_ANALYSIS_AVAILABLE:
            raise RuntimeError("Anti-formula analysis not available")

        print("=" * 80)
        print("Running Anti-Formula Analysis")
        print("=" * 80)

        results = extract_anti_arguments(
            model_files=model_files,
            project_root=self.project_root,
            output_dir=output_dir,
            formulas=formulas
        )

        self.results['anti_formula'] = results
        return results

    def run_all(self, **kwargs) -> Dict:
        """
        Run all available analyses.

        Args:
            **kwargs: Arguments passed to individual analyses

        Returns:
            Dictionary containing all analysis results
        """
        print("=" * 80)
        print("Running All Analyses")
        print("=" * 80)

        # Run popularity bias analysis
        if POPULARITY_BIAS_AVAILABLE:
            self.run_popularity_bias_analysis(
                data_dir=kwargs.get('popularity_data_dir'),
                results_dir=kwargs.get('popularity_results_dir'),
                configure_logging=kwargs.get('configure_logging', True)
            )

        # Run anti-formula analysis
        if ANTI_ANALYSIS_AVAILABLE:
            self.run_anti_formula_analysis(
                model_files=kwargs.get('model_files'),
                output_dir=kwargs.get('anti_results_dir'),
                formulas=kwargs.get('formulas')
            )

        print("=" * 80)
        print("All analyses complete!")
        print("=" * 80)

        return self.results


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='LLM Consensus Analysis Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run popularity bias analysis only
  python analyze.py popularity

  # Run anti-formula analysis only
  python analyze.py anti --formulas 4 5

  # Run all analyses
  python analyze.py all

  # Specify custom directories
  python analyze.py popularity --data-dir ./custom/data --results-dir ./custom/results
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Analysis command')

    # Popularity bias analysis
    popularity_parser = subparsers.add_parser(
        'popularity',
        help='Run popularity bias analysis (robust regression)'
    )
    popularity_parser.add_argument(
        '--data-dir',
        help='Directory containing input data'
    )
    popularity_parser.add_argument(
        '--results-dir',
        help='Directory for output results'
    )
    popularity_parser.add_argument(
        '--no-logging',
        action='store_true',
        help='Disable logging configuration'
    )

    # Anti-formula analysis
    anti_parser = subparsers.add_parser(
        'anti',
        help='Run anti-formula analysis'
    )
    anti_parser.add_argument(
        '--formulas',
        type=int,
        nargs='+',
        default=[4, 5],
        help='Formula numbers to extract arguments for (default: 4 5)'
    )
    anti_parser.add_argument(
        '--output-dir',
        help='Directory for output results'
    )

    # Run all analyses
    all_parser = subparsers.add_parser(
        'all',
        help='Run all available analyses'
    )
    all_parser.add_argument(
        '--popularity-data-dir',
        help='Directory containing popularity bias input data'
    )
    all_parser.add_argument(
        '--popularity-results-dir',
        help='Directory for popularity bias output results'
    )
    all_parser.add_argument(
        '--anti-results-dir',
        help='Directory for anti-formula output results'
    )
    all_parser.add_argument(
        '--formulas',
        type=int,
        nargs='+',
        default=[4, 5],
        help='Formula numbers for anti-formula analysis (default: 4 5)'
    )
    all_parser.add_argument(
        '--no-logging',
        action='store_true',
        help='Disable logging configuration'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    pipeline = AnalysisPipeline()

    if args.command == 'popularity':
        pipeline.run_popularity_bias_analysis(
            data_dir=args.data_dir,
            results_dir=args.results_dir,
            configure_logging=not args.no_logging
        )

    elif args.command == 'anti':
        pipeline.run_anti_formula_analysis(
            formulas=args.formulas,
            output_dir=args.output_dir
        )

    elif args.command == 'all':
        pipeline.run_all(
            popularity_data_dir=args.popularity_data_dir,
            popularity_results_dir=args.popularity_results_dir,
            anti_results_dir=args.anti_results_dir,
            formulas=args.formulas,
            configure_logging=not args.no_logging
        )


if __name__ == "__main__":
    main()