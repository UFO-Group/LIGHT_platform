"""
Extract arguments against Formula 4 and Formula 5 from LLM output files.
Creates anti-Formula 4.md and anti-Formula 5.md with collected arguments.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Default model files to process
DEFAULT_MODEL_FILES = {
    "gpt-5": "gpt-5.md",
    "grok-4": "grok-4.md",
    "claude-opus-4-5": "claude-opus-4-5-20251101.md",
    "gemini-3-pro": "gemini-3-pro-preview.md"
}

# Negative keywords to look for near Formula 4/5 mentions
NEGATIVE_KEYWORDS = [
    "lacks", "poor", "weak", "risk", "concern", "limit", "reject",
    "marginal", "moderate", "deficit", "low", "lower", "limited",
    "however", "but", "compromis", "challeng", "issue", "problem",
    "difficult", "uncertain", "unpredictable", "swelling.*risk",
    "thrombogen", "inflamm", "fail", "outperform", "second.place",
    "runner.up", "less", "trade.off", "challenge", "constrain"
]


class AntiArgumentExtractor:
    """Extract arguments against specific formulas from LLM outputs."""

    def __init__(
        self,
        model_files: Dict[str, str] = None,
        project_root: str = None,
        output_dir: str = None
    ):
        """
        Initialize the argument extractor.

        Args:
            model_files: Dictionary mapping model names to their output files
            project_root: Root directory of the project (default: auto-detect)
            output_dir: Directory for output results (default: <project_root>/anti_analysis/results)
        """
        self.model_files = model_files or DEFAULT_MODEL_FILES

        # Auto-detect project root if not provided
        if project_root is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))

        self.project_root = project_root
        self.output_dir = output_dir or os.path.join(project_root, "anti_analysis", "results")
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_runs_from_file(self, filepath: str) -> List[Tuple[str, str]]:
        """Split file content into individual runs."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by Run markers
        runs = re.split(r'# Run (\d+) response', content)[1:]  # Skip header

        run_data = []
        for i in range(0, len(runs), 2):
            if i + 1 < len(runs):
                run_num = runs[i].strip()
                run_content = runs[i + 1]
                # Remove CSV blocks to avoid noise
                run_content = re.sub(r'```csv.*?```', '', run_content, flags=re.DOTALL)
                run_data.append((run_num, run_content))

        return run_data

    def extract_formula_arguments(self, run_content: str, formula_num: int) -> List[str]:
        """
        Extract arguments against a specific formula from run content.
        Looks for mentions of the formula with negative context.
        """
        arguments = []

        # Pro-positive keywords to EXCLUDE (these indicate support, not opposition)
        SUPPORT_KEYWORDS = [
            "winner", "selected", "best", "excellent", "optimal", "superior",
            "achieves", "delivers", "balanced", "highest score", "one.sentence rationale"
        ]

        # Pattern to find Formula X mentions with surrounding context
        patterns = [
            # Rejected candidates section
            rf'Formula {formula_num}[^.\n]*?:\s*([^\n]*?(?:{"|".join(NEGATIVE_KEYWORDS)})[^\n]*)',
            # Bullet points with Formula X
            rf'[-*]\s*Formula {formula_num}[^.\n]*?:\s*([^\n]+)',
            # Formula X in sentences with negative keywords
            rf'Formula {formula_num}[^.\n]*\s+(?:{"|".join(NEGATIVE_KEYWORDS)})[^.\n]*\.',
            # Formula X followed by negative description
            rf'Formula {formula_num}\s*\([^)]+\)[^.]*\.(?:\s*[^.]*?(?:{"|".join(NEGATIVE_KEYWORDS)})[^.]*\.)*',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, run_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                arg_text = match.group(0) if match.groups() else match.group(0)
                # Clean up the argument
                arg_text = arg_text.strip()

                # Filter out CSV data
                if re.search(r'\d+,\s*\d+,\s*\d+', arg_text):
                    continue

                # Filter out support statements (winner/selected/best/etc)
                if any(sup in arg_text.lower() for sup in SUPPORT_KEYWORDS):
                    continue

                # Must have negative keywords
                if len(arg_text) > 15 and any(neg in arg_text.lower() for neg in NEGATIVE_KEYWORDS):
                    # Avoid duplicates
                    if not any(arg_text[:50] in existing for existing in arguments):
                        arguments.append(arg_text)

        return arguments

    def extract_from_rejected_section(self, run_content: str, formula_num: int) -> List[str]:
        """Extract arguments from 'REJECTED CANDIDATES' or similar sections."""
        arguments = []

        # Find rejected/autopsy sections
        sections = re.finditer(
            r'REJECTED.*?(?=\n#|\n\n\n|$)',
            run_content,
            re.IGNORECASE | re.DOTALL
        )

        for section in sections:
            section_text = section.group(0)
            # Look for Formula X mentions
            formula_mentions = re.finditer(
                rf'Formula {formula_num}[^.\n]*[.:]\s*([^\n]+)',
                section_text,
                re.IGNORECASE
            )
            for mention in formula_mentions:
                arg = mention.group(0).strip()

                # Filter out CSV data
                if re.search(r'\d+,\s*\d+,\s*\d+', arg):
                    continue

                # Clean up bullet points
                arg = re.sub(r'^[-*•]\s*', '', arg)

                if len(arg) > 15:
                    arguments.append(arg)

        return arguments

    def extract_from_rationale_tables(self, run_content: str, formula_num: int) -> List[str]:
        """Extract negative rationale from Claude-style tables."""
        arguments = []

        # Look for table rows with Formula X and negative/score info
        # Claude format: | **Formula X** | score | rationale |
        pattern = rf'\|\s*\*?\*?Formula {formula_num}\*?\*?[^|]*\|[^|]*\|[^|]*\|([^|]+)\|'

        matches = re.finditer(pattern, run_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            rationale = match.group(1).strip()

            # Filter out CSV data
            if re.search(r'\d+,\s*\d+,\s*\d+', rationale):
                continue

            # Check if rationale contains negative indicators
            if any(neg in rationale.lower() for neg in ["limit", "lack", "poor", "weak", "risk", "concern"]):
                arguments.append(f"Rationale: {rationale}")

        return arguments

    def extract_comparative_arguments(self, run_content: str, formula_num: int) -> List[str]:
        """Extract arguments where other formulas are preferred over Formula X."""
        arguments = []

        # Look for "X better than Formula X" patterns
        patterns = [
            rf'(?:winner|selected|preferred)[^.]*\b(?:than|over|versus)\s*Formula {formula_num}[^.]*\.',
            rf'Formula {formula_num}[^.]*\b(?:outperform|beat|surpass)[^.]*\.',
            rf'Formula {formula_num}[^.]*\b(?:lose|lost|second|runner.up|reject)[^.]*\.',
            rf'Formula {formula_num}[^.]*\b(?:however|but)\s+[^.]*?(?:{"|".join(NEGATIVE_KEYWORDS)})[^.]*\.',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, run_content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                arg = match.group(0).strip()

                # Filter out CSV data
                if re.search(r'\d+,\s*\d+,\s*\d+', arg):
                    continue

                if len(arg) > 20:
                    arguments.append(arg)

        return arguments

    def process_model(self, model_name: str, filepath: str) -> Tuple[List[str], List[str]]:
        """Process a single model file and extract arguments."""
        all_args_4 = []
        all_args_5 = []

        try:
            runs = self.extract_runs_from_file(filepath)

            for run_num, run_content in runs:
                # Extract arguments against Formula 4
                args_4 = self.extract_formula_arguments(run_content, 4)
                args_4.extend(self.extract_from_rejected_section(run_content, 4))
                args_4.extend(self.extract_from_rationale_tables(run_content, 4))
                args_4.extend(self.extract_comparative_arguments(run_content, 4))

                for arg in args_4:
                    all_args_4.append(f"{model_name} Run {run_num}: {arg}")

                # Extract arguments against Formula 5
                args_5 = self.extract_formula_arguments(run_content, 5)
                args_5.extend(self.extract_from_rejected_section(run_content, 5))
                args_5.extend(self.extract_from_rationale_tables(run_content, 5))
                args_5.extend(self.extract_comparative_arguments(run_content, 5))

                for arg in args_5:
                    all_args_5.append(f"{model_name} Run {run_num}: {arg}")

        except Exception as e:
            print(f"  Error processing {model_name}: {e}")
            return [], []

        return all_args_4, all_args_5

    def deduplicate_arguments(self, arguments: List[str]) -> List[str]:
        """Remove duplicate arguments while preserving order."""
        seen = set()
        unique = []
        for arg in arguments:
            # Create a normalized key for comparison
            key = re.sub(r'\s+', ' ', arg.lower().strip())
            key = re.sub(r'run \d+:', '', key)  # Remove run number for comparison
            if key and key not in seen and len(key) > 20:
                seen.add(key)
                unique.append(arg)
        return unique

    def write_anti_formula_file(self, formula_num: int, arguments: List[str]) -> str:
        """Write the collected arguments to a markdown file."""
        filename = os.path.join(self.output_dir, f"anti-Formula {formula_num}.md")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Arguments Against Formula {formula_num}\n\n")
            f.write(f"*Extracted from LLM consensus analysis*\n\n")
            f.write(f"Total unique arguments found: {len(arguments)}\n\n")
            f.write("---\n\n")

            for arg in arguments:
                # Clean up formatting
                arg = arg.strip()
                # Remove extra bullet points if present
                arg = re.sub(r'^[-*•]\s*', '', arg)
                # Remove "Rationale:" prefix if present
                arg = re.sub(r'^Rationale:\s*', '', arg)
                # Remove duplicate leading dashes
                arg = re.sub(r'^-+', '', arg).strip()

                f.write(f"- {arg}\n")

        print(f"  Written {len(arguments)} arguments to {filename}")
        return filename

    def extract(self, formulas: List[int] = None) -> Dict[int, List[str]]:
        """
        Extract arguments against specified formulas.

        Args:
            formulas: List of formula numbers to extract arguments for (default: [4, 5])

        Returns:
            Dictionary mapping formula numbers to lists of unique arguments
        """
        if formulas is None:
            formulas = [4, 5]

        # Change to project root for relative file paths
        original_cwd = os.getcwd()
        try:
            os.chdir(self.project_root)

            all_arguments = {formula_num: [] for formula_num in formulas}

            # Process each model
            for model_name, filename in self.model_files.items():
                if not os.path.exists(filename):
                    print(f"  WARNING: {filename} not found, skipping...")
                    continue

                print(f"Processing {model_name}...")
                args_4, args_5 = self.process_model(model_name, filename)
                all_arguments[4].extend(args_4)
                all_arguments[5].extend(args_5)

            # Deduplicate
            print("\nDeduplicating arguments...")
            unique_arguments = {}
            for formula_num in formulas:
                unique_arguments[formula_num] = self.deduplicate_arguments(all_arguments[formula_num])

            # Write output files
            print("\nWriting output files...")
            for formula_num in formulas:
                self.write_anti_formula_file(formula_num, unique_arguments[formula_num])

            print("\n" + "=" * 60)
            print(f"Extraction complete!")
            for formula_num in formulas:
                print(f"  anti-Formula {formula_num}.md: {len(unique_arguments[formula_num])} unique arguments")
            print("\nNOTE: Some arguments may be duplicates or need manual cleanup.")
            print("Please review the generated files and add any missing arguments manually.")

            return unique_arguments

        finally:
            os.chdir(original_cwd)


def extract_anti_arguments(
    model_files: Dict[str, str] = None,
    project_root: str = None,
    output_dir: str = None,
    formulas: List[int] = None
) -> Dict[int, List[str]]:
    """
    Convenience function to extract arguments against specified formulas.

    Args:
        model_files: Dictionary mapping model names to their output files
        project_root: Root directory of the project (default: auto-detect)
        output_dir: Directory for output results (default: <project_root>/anti_analysis/results)
        formulas: List of formula numbers to extract arguments for (default: [4, 5])

    Returns:
        Dictionary mapping formula numbers to lists of unique arguments
    """
    extractor = AntiArgumentExtractor(
        model_files=model_files,
        project_root=project_root,
        output_dir=output_dir
    )
    return extractor.extract(formulas=formulas)


def main():
    """Main entry point for command line usage."""
    print("Extracting arguments against Formula 4 and Formula 5...")
    print("=" * 60)
    extract_anti_arguments()


if __name__ == "__main__":
    main()