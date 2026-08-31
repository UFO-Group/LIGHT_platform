"""
Anti-Formula Analysis Module

Provides functionality for extracting arguments against specific formulas
from LLM output files.
"""

from .analysis.extract_arguments import extract_anti_arguments, AntiArgumentExtractor

__version__ = "1.0.0"
__all__ = [
    "extract_anti_arguments",
    "AntiArgumentExtractor"
]