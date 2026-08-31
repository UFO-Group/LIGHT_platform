"""
Shared utilities and configuration for LLM reliability visualization modules
"""

import json
import sys
import io
from pathlib import Path
from typing import Dict

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Color scheme for models
MODEL_COLORS = {
    'gpt-5': '#FF6B6B',
    'grok-4': '#4ECDC4',
    'claude-opus-4-5-20251101': '#45B7D1',
    'gemini-3-pro-preview': '#FFA07A'
}

# English model names for display
MODEL_NAMES = {
    'gpt-5': 'GPT-5',
    'grok-4': 'Grok-4',
    'claude-opus-4-5-20251101': 'Claude Opus 4.5',
    'gemini-3-pro-preview': 'Gemini 3 Pro'
}

# English criterion names
CRITERION_NAMES = {
    'Mechanical_Safety': 'Mechanical Safety',
    'Swelling_Performance': 'Swelling Performance',
    'Endothelialization': 'Endothelialization',
    'SMC_inhibition': 'SMC Inhibition',
    'Anti_inflammation': 'Anti-inflammation',
    'Thrombogenicity': 'Thrombogenicity',
    'Total_Score': 'Total Score'
}


def load_analysis_data(base_dir: str = ".") -> Dict:
    """
    Load analysis results data from JSON file

    Parameters
    ----------
    base_dir : str
        Base directory path (default: current directory)

    Returns
    -------
    Dict
        Analysis results data

    Raises
    ------
    FileNotFoundError
        If data file does not exist
    """
    data_file = Path(base_dir) / "reliability_analysis_results.json"

    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def get_output_dir(base_dir: str = ".") -> Path:
    """
    Get or create output directory for visualizations

    Parameters
    ----------
    base_dir : str
        Base directory path (default: current directory)

    Returns
    -------
    Path
        Output directory path
    """
    output_dir = Path(base_dir) / "visualizations"
    output_dir.mkdir(exist_ok=True)
    return output_dir
