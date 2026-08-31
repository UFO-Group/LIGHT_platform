"""
Report Generation Module for LLM Consensus Reliability Analysis

This module provides functionality for generating reports in LaTeX format:
- Chinese version (CLLM_Reliability_Report.tex)
- English version (LLM_Reliability_Report_EN.tex)

Usage:
    from reporting import generate_tex, generate_tex_en

    # Generate Chinese LaTeX report
    generate_tex.main()

    # Generate English LaTeX report
    generate_tex_en.main()
"""

from . import generate_tex
from . import generate_tex_en

__all__ = ['generate_tex', 'generate_tex_en']
