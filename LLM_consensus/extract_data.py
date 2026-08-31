"""
LLM Consensus Data Extractor
Extract and normalize data from markdown files
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import io

# Set stdout to UTF-8 encoding (fixes Windows encoding issues)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class LLMDataExtractor:
    """Extract data from LLM output files"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.models = ["gpt-5", "grok-4", "claude-opus-4-5-20251101", "gemini-3-pro-preview"]
        self.criteria = [
            "Mechanical_Safety",
            "Swelling_Performance",
            "Endothelialization",
            "SMC_inhibition",
            "Anti_inflammation",
            "Thrombogenicity",
            "Total_Score"
        ]

    def extract_formula_number(self, text: str) -> Optional[int]:
        """
        Extract formula number from text

        Supports multiple formats:
        - "Formula 5"
        - "Formula 5 (GelMA & PEG)"
        - "GelMA & PEG [Formula 5]"
        - "Formula 4: GelMA & Silk"

        Args:
            text: Text containing formula information

        Returns:
            Formula number (1-10), returns None if not found
        """
        # Try multiple pattern matching
        patterns = [
            r'Formula\s*(\d+)',  # "Formula 5"
            r'\[Formula\s*(\d+)\]',  # "[Formula 5]"
            r'formula\s*(\d+)',  # "formula 5" (lowercase)
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    num = int(match.group(1))
                    if 1 <= num <= 10:
                        return num
                except (ValueError, IndexError):
                    continue

        return None

    def extract_run_number(self, run_header: str) -> int:
        """
        Extract run number from run header

        Args:
            run_header: Run header text, e.g., "# Run 0 response"

        Returns:
            Run number
        """
        match = re.search(r'Run\s*(\d+)', run_header, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return -1

    def extract_data_from_md(self, model_name: str) -> Optional[pd.DataFrame]:
        """
        Extract data from markdown file

        Args:
            model_name: Model name

        Returns:
            DataFrame with extracted data, returns None if file not found or extraction failed
        """
        file_path = self.base_dir / f"{model_name}.md"

        if not file_path.exists():
            print(f"Warning: {file_path} does not exist")
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract data for each run
        # Try multiple separator patterns
        patterns = [
            r'# Run (\d+) response',  # Standard: "# Run 0 response"
            r'Run (\d+)',  # Simplified: "Run 0"
        ]

        runs = []
        for pattern in patterns:
            runs = re.split(pattern, content)
            if len(runs) > 1:
                break

        runs = [r for r in runs if r.strip()]
        data_records = []

        for i in range(0, len(runs), 2):
            if i + 1 >= len(runs):
                break

            run_num = int(runs[i].strip().split('Temperature')[0].strip())
            run_content = runs[i + 1]

            # Extract CSV data
            csv_match = re.search(r'```csv\s*\n(.*?)```', run_content, re.DOTALL)
            if not csv_match:
                continue

            csv_text = csv_match.group(1)
            lines = [line.strip() for line in csv_text.split('\n') if line.strip()]

            if len(lines) < 2:
                continue

            # Parse CSV headers
            headers = [h.strip() for h in lines[0].split(',')]

            # Parse each data row
            for line in lines[1:]:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 8:
                    formula = parts[0]
                    # Extract Formula number
                    formula_num = self.extract_formula_number(formula)
                    if formula_num is None:
                        continue

                    scores = {
                        'Model': model_name,
                        'Run': run_num,
                        'Formula': formula_num,
                        'Formula_Name': formula
                    }

                    # Extract each score
                    for j, criterion in enumerate(self.criteria):
                        if j + 1 < len(parts):
                            try:
                                scores[criterion] = float(parts[j + 1])
                            except ValueError:
                                scores[criterion] = np.nan

                    data_records.append(scores)

            # Extract winner formula - try multiple patterns
            winner_patterns = [
                r'Selected Formula[:\s]+(.*?)(?:\n|One-Sentence)',
                r'Selected Formula[:\s]+\*\*(.*?)\*\*',
                r'\*\*Selected Formula:\*\*\s*(.*?)(?:\n|One-Sentence)',
            ]

            winner_num = None
            for pattern in winner_patterns:
                winner_match = re.search(pattern, run_content, re.IGNORECASE | re.DOTALL)
                if winner_match:
                    winner_text = winner_match.group(1).strip()
                    winner_num = self.extract_formula_number(winner_text)
                    if winner_num is not None:
                        break

            # Add Winner field to all records for this run
            for record in data_records:
                if record['Run'] == run_num:
                    record['Winner'] = winner_num

        if not data_records:
            return None

        df = pd.DataFrame(data_records)
        return df

    def extract_and_save_all(self) -> Dict[str, pd.DataFrame]:
        """
        Extract and save data from all models

        Returns:
            Dictionary with model names as keys and DataFrames as values
        """
        print("=" * 80)
        print("LLM Data Extractor")
        print("=" * 80)

        all_data = {}

        for model in self.models:
            print(f"\nProcessing {model}...")
            df = self.extract_data_from_md(model)
            if df is not None:
                all_data[model] = df
                print(f"  ✓ Successfully extracted {len(df)} records, {df['Run'].nunique()} runs")

                # Check Winner field
                winner_counts = df[df['Winner'].notna()].groupby('Run')['Winner'].first()
                print(f"    - Extracted {len(winner_counts)} winning formulas")

                # Check missing winners
                missing_winners = df['Run'].nunique() - len(winner_counts)
                if missing_winners > 0:
                    print(f"    ⚠ Warning: {missing_winners} runs missing winner information")
            else:
                print(f"  ✗ Extraction failed")

        # Save as JSON
        self.save_to_json(all_data)

        # Save as CSV (one file per model)
        self.save_to_csv(all_data)

        print(f"\nTotal extracted data from {len(all_data)} models")
        return all_data

    def save_to_json(self, all_data: Dict[str, pd.DataFrame]) -> None:
        """Save as JSON format"""
        output_path = self.base_dir / "extracted_data.json"

        export_data = {}
        for model, df in all_data.items():
            # Convert DataFrame to list of dicts, handle NaN values
            export_data[model] = df.to_dict('records')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=self.json_serializer)
        print(f"\nData saved to: {output_path}")

    @staticmethod
    def json_serializer(obj):
        """JSON serializer for numpy and pandas types"""
        if isinstance(obj, (np.integer, np.floating)):
            if np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def save_to_csv(self, all_data: Dict[str, pd.DataFrame]) -> None:
        """Save as CSV format (one file per model)"""
        output_dir = self.base_dir / "extracted_csv"
        output_dir.mkdir(exist_ok=True)

        for model, df in all_data.items():
            output_path = output_dir / f"{model}.csv"
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"  CSV saved: {output_path}")

        # Also save a merged CSV
        merged_df = pd.concat(all_data.values(), ignore_index=True)
        output_path = output_dir / "all_models.csv"
        merged_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"  Merged CSV saved: {output_path}")


def main():
    """Main function"""
    print("Starting LLM data extraction...")

    extractor = LLMDataExtractor()
    all_data = extractor.extract_and_save_all()

    if all_data:
        print("\n" + "=" * 80)
        print("Data extraction complete!")
        print("=" * 80)

        # Print statistics
        print("\nData statistics:")
        for model, df in all_data.items():
            print(f"\n{model}:")
            print(f"  Total records: {len(df)}")
            print(f"  Number of runs: {df['Run'].nunique()}")
            print(f"  Number of formulas: {df['Formula'].nunique()}")
            print(f"  Records with Winner: {df['Winner'].notna().sum()}")
    else:
        print("\nError: Failed to extract any data")


if __name__ == "__main__":
    main()