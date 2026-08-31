#!/usr/bin/env python3
"""
LLM Consensus Reliability Analysis - One-Click Pipeline

One-click run complete analysis workflow:
1. Data extraction
2. Reliability analysis
3. Generate visualizations
4. Generate LaTeX reports
5. Compile PDF (optional)

Usage:
    python run_pipeline.py              # Run all steps
    python run_pipeline.py --no-pdf     # Skip PDF compilation
    python run_pipeline.py --skip-extraction  # Skip data extraction
"""

import sys
import json
from pathlib import Path

# Set UTF-8 encoding (Windows only)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for Python 3.6 and below
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_header(text):
    """Print section header"""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")


# ============================================================================
# Data Fix Module
# ============================================================================

def fix_gpt5_run5_winner():
    """
    Fix GPT-5 Run 5 Winner data

    Problem description:
    In GPT-5's Run 5 response, the "Selected Formula" field lacks the formula number
    (format is "Gelatin_methacrylate (GelMA) & Polyethylene_glycol (PEG)")
    causing automatic extraction to fail, Winner value is NaN.

    Solution:
    Manually set Run 5's Winner to 5 (consistent with other runs, as materials are the same)

    Note:
    - Do not modify original .md files per user instructions
    - This function runs after data extraction and before analysis
    - Can be disabled by commenting out the caller below
    """
    print_header("Data Fix")

    try:
        # Read extracted data
        data_file = Path('extracted_data.json')
        if not data_file.exists():
            print("[WARNING] extracted_data.json does not exist, skipping fix")
            return False

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Fix GPT-5 Run 5 Winner
        gpt5_records = data['gpt-5']
        fixed_count = 0

        for record in gpt5_records:
            if record['Run'] == 5:
                # Check if Winner is NaN or None
                winner = record.get('Winner')
                if winner is None or (isinstance(winner, float) and str(winner) == 'nan'):
                    record['Winner'] = 5
                    fixed_count += 1

        if fixed_count > 0:
            # Save fixed data
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"[OK] Fixed {fixed_count} records for GPT-5 Run 5")
            print("[OK] Winner set to 5 (GelMA & PEG)")
            print("\nNote: GPT-5 Run 5's Selected Formula is")
            print("      'Gelatin_methacrylate (GelMA) & Polyethylene_glycol (PEG)'")
            print("      Same materials as Formula 5, so set Winner = 5")
            return True
        else:
            print("[INFO] GPT-5 Run 5 data is normal, no fix needed")
            return True

    except Exception as e:
        print(f"[ERROR] Data fix failed: {e}")
        return False


# ============================================================================
# Module Execution Functions
# ============================================================================

def run_module(module_name, step_name, step_num):
    """Run a single module"""
    print_header(f"Step {step_num}: {step_name}")
    try:
        module = __import__(module_name, fromlist=['main'])
        module.main()
        print(f"[OK] {step_name} completed\n")
        return True
    except Exception as e:
        print(f"[ERROR] {step_name} failed: {e}\n")
        return False


def main():
    """Main function"""
    print("=" * 80)
    print("LLM Consensus Reliability Analysis - Pipeline")
    print("=" * 80)

    steps = [
        ("reliability_analysis.extract_data", "Data Extraction", 1),
        ("reliability_analysis.analyze_reliability", "Reliability Analysis", 2),
        ("example_visualization", "Generate Visualizations", 3),
        ("reporting.generate_tex", "Generate Chinese Report", 4),
        ("reporting.generate_tex_en", "Generate English Report", 5),
    ]

    completed = 0

    # ============================================================================
    # Data Fix Step (optional, can be commented out)
    # ============================================================================
    # Fix known data issues after extraction and before analysis
    # ============================================================================
    if run_module("reliability_analysis.extract_data", "Data Extraction", 1):
        completed += 1

        # Execute data fix (fix GPT-5 Run 5 Winner data)
        # To disable, comment out the line below
        fix_gpt5_run5_winner()
        # To disable, comment out the line above

    # Continue with other steps
    for module, name, num in steps[1:]:
        if run_module(module, name, num):
            completed += 1

    # Summary
    print_header("Execution Summary")
    print(f"Successfully completed {completed}/{len(steps)} steps")

    if completed == len(steps):
        print("\n[OK] All steps completed successfully!")
        print("\nGenerated files:")
        print("  - extracted_data.json")
        print("  - reliability_analysis_results.json")
        print("  - visualizations/*.png")
        print("  - LLM_Reliability_Report.tex / .pdf")
        print("  - LLM_Reliability_Report_EN.tex / .pdf")
        return 0
    else:
        print(f"\n[ERROR] {len(steps) - completed} step(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
