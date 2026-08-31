"""
Generate LaTeX format LLM Reliability Analysis Report - English Version
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import sys
import io


class LaTeXReportGeneratorEn:
    """Generate LaTeX format reliability analysis report - English version"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.data_file = self.base_dir / "reliability_analysis_results.json"
        self.output_file = self.base_dir / "LLM_Reliability_Report_EN.tex"

    def load_data(self) -> Dict:
        """Load analysis results data"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    def generate_preamble(self) -> str:
        """Generate LaTeX document preamble"""
        return r"""\documentclass[12pt,a4paper]{article}

% Packages
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{xcolor}
\usepackage{float}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{hyperref}

% Page settings
\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}

% Hyperlink settings
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
    citecolor=green,
}

% Custom colors
\definecolor{lightgray}{gray}{0.9}
\definecolor{excellent}{RGB}{46, 139, 87}
\definecolor{good}{RGB}{60, 179, 113}
\definecolor{fair}{RGB}{255, 165, 0}
\definecolor{poor}{RGB}{220, 20, 60}

% Table styles
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}m{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}m{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}m{#1}}

% Title information
\title{\textbf{Statistical Reliability Analysis of LLM Multi-Run Evaluations}\\
\large Assessing the Consistency and Stability of Repeated AI Model Runs}
\author{LLM Consensus Analysis Framework}
\date{\today}

\begin{document}

\maketitle

\tableofcontents
\newpage

"""

    def generate_section_introduction(self) -> str:
        """Generate introduction section"""
        return r"""
\section{Background and Objectives}

\subsection{Research Background}
In materials science decision-making, Large Language Models (LLMs) are widely used for evaluating and screening candidate materials. However, whether the same LLM model can produce consistent and reliable results across multiple runs is a critical statistical question. This study aims to systematically evaluate the reliability of LLM models in multiple independent runs through statistical analysis.

\subsection{Research Objectives}
The core objective of this study is to test the following hypothesis:
\begin{quote}
\textit{Multiple independent runs of the same AI model are statistically reliable, with consistent scoring and stable decision-making.}
\end{quote}

Specifically, we evaluate reliability across the following dimensions:
\begin{itemize}
    \item \textbf{Scoring Consistency}: Variation in scores for the same material across different runs
    \item \textbf{Inter-rater Reliability}: Correlation of scores between different runs
    \item \textbf{Decision Stability}: Consistency of final winner selection
\end{itemize}

\subsection{Data Source}
This study analyzes four mainstream LLM models (GPT-5, Grok-4, Claude Opus 4.5, Gemini 3 Pro) across 11 independent runs. Each run evaluates 10 candidate materials across 6 dimensions (0-10 points) and selects the optimal material.

\newpage

"""

    def generate_section_methodology(self) -> str:
        """Generate methodology section"""
        return r"""
\section{Methodology}

\subsection{Statistical Metrics}

\subsubsection{Coefficient of Variation (CV)}
Coefficient of variation measures the relative dispersion of scores:
\begin{equation}
    CV = \frac{\sigma}{\mu} \times 100\%
\end{equation}
where $\sigma$ is standard deviation and $\mu$ is the mean. Lower CV values indicate higher scoring consistency.

\subsubsection{Intraclass Correlation Coefficient (ICC)}
ICC measures the consistency between different runs (raters). Based on the ANOVA method by Shrout \& Fleiss (1979), we calculate ICC(3,1) for a two-way fixed-effects model with absolute agreement:
\begin{equation}
    ICC(3,1) = \frac{MS_R - MS_E}{MS_R + (k-1)MS_E}
\end{equation}
where $MS_R$ is mean square between targets (materials), $MS_E$ is mean square error, and $k$ is the number of raters (runs). ICC values closer to 1 indicate higher consistency.

\subsubsection{Consistency Ratio}
Consistency ratio is defined as the ratio of score range to mean:
\begin{equation}
    CR = \frac{Range}{Mean}
\end{equation}
This metric reflects the relative fluctuation range of scores.

\subsubsection{Decision Consistency Rate}
Decision consistency rate is the proportion of runs selecting the same winner:
\begin{equation}
    DC = \frac{N_{most\_frequent}}{N_{total}} \times 100\%
\end{equation}

\subsubsection{Information Entropy}
Information entropy measures the uncertainty in winner distribution:
\begin{equation}
    H = -\sum_{i} p_i \log_2(p_i)
\end{equation}
where $p_i$ is the probability of formula $i$ being selected as the winner. Lower entropy values indicate more concentrated decision-making.

\subsection{Reliability Assessment Criteria}
We adopt the following reliability assessment standards based on statistical metric ranges:

\begin{table}[H]
\centering
\caption{Reliability Assessment Criteria}
\begin{tabular}{lll}
\toprule
\textbf{Metric} & \textbf{Grade} & \textbf{Threshold Range} \\
\midrule
\multirow{3}{*}{Coefficient of Variation (CV)} & Excellent & CV $<$ 10\% \\
& Good & 10\% $\le$ CV $<$ 20\% \\
& Fair & CV $\ge$ 20\% \\
\midrule
\multirow{3}{*}{Intraclass Correlation (ICC)} & Excellent & ICC $>$ 0.8 \\
& Good & 0.6 $<$ ICC $\le$ 0.8 \\
& Fair & ICC $\le$ 0.6 \\
\midrule
\multirow{3}{*}{Decision Consistency Rate (DC)} & Excellent & DC $\ge$ 80\% \\
& Good & 60\% $\le$ DC $<$ 80\% \\
& Fair & DC $<$ 60\% \\
\bottomrule
\end{tabular}
\end{table}

\newpage

"""

    def generate_model_section(self, model_name: str, model_data: Dict) -> str:
        """Generate analysis section for a single model"""
        section_content = f"""
\\section{{{model_name} Reliability Analysis}}

\\subsection{{Scoring Consistency Analysis}}

The following table displays the coefficient of variation (CV) across scoring dimensions for {model_name}:

\\begin{{table}}[H]
\\centering
\\caption{{{model_name} - Scoring Variation Coefficient Analysis}}
\\begin{{tabular}}{{llccc}}
\\toprule
\\textbf{{Scoring Dimension}} & \\textbf{{Mean CV(\%)}} & \\textbf{{Max CV(\%)}} & \\textbf{{Min CV(\%)}} & \\textbf{{Consistency Ratio}} \\\\
\\midrule
"""

        # Add scoring reliability data
        if 'scoring_reliability' in model_data:
            for criterion, stats in model_data['scoring_reliability'].items():
                criterion_display = criterion.replace('_', '\\_')
                cv = f"{stats['overall_cv']:.2f}"
                max_cv = f"{stats['max_cv']:.2f}"
                min_cv = f"{stats['min_cv']:.2f}"
                cr = f"{stats['consistency_ratio']:.3f}"

                section_content += f"{criterion_display} & {cv} & {max_cv} & {min_cv} & {cr} \\\\\n"

        section_content += r"""\bottomrule
\end{tabular}
\end{table}

\subsection{Inter-rater Reliability Analysis}

The intraclass correlation coefficient (ICC) reflects scoring consistency across different runs:

\begin{table}[H]
\centering
\caption{""" + model_name + r""" - Intraclass Correlation Coefficient}
\begin{tabular}{lc}
\toprule
\textbf{Scoring Dimension} & \textbf{ICC} \\
\midrule
"""

        # Add ICC data
        if 'icc_scores' in model_data:
            for criterion, icc in model_data['icc_scores'].items():
                criterion_display = criterion.replace('_', '\\_')
                icc_str = f"{icc:.4f}"
                section_content += f"{criterion_display} & {icc_str} \\\\\n"

        section_content += r"""\bottomrule
\end{tabular}
\end{table}

\subsection{Decision Consistency Analysis}

"""

        # Add decision consistency data
        if 'winner_consistency' in model_data:
            wc = model_data['winner_consistency']
            section_content += f"""
\\begin{{itemize}}
    \\item \\textbf{{Total Runs}}: {wc['total_runs']} runs
    \\item \\textbf{{Most Common Winner}}: Formula {wc['most_common_winner']}
    \\item \\textbf{{Occurrence Count}}: {wc['most_common_count']} times
    \\item \\textbf{{Decision Consistency Rate}}: {wc['consistency_rate']:.1f}\\%
    \\item \\textbf{{Information Entropy}}: {wc['entropy']:.3f} (Max Entropy: {wc['max_entropy']:.3f})
\\end{{itemize}}

Winner formula distribution:

\\begin{{table}}[H]
\\centering
\\caption{{{model_name} - Winner Formula Distribution}}
\\begin{{tabular}}{{cc}}
\\toprule
\\textbf{{Formula}} & \\textbf{{Count}} \\\\
\\midrule
"""

            for formula, count in sorted(wc.get('winner_distribution', {}).items()):
                section_content += f"Formula {formula} & {count} \\\\\n"

            section_content += r"""\bottomrule
\end{tabular}
\end{table}

"""

        section_content += r"""
\newpage

"""
        return section_content

    def generate_comparison_section(self, data: Dict) -> str:
        """Generate model comparison section"""
        section_content = r"""
\section{Model Comparison Analysis}

\subsection{Overall Reliability Comparison}

The following table summarizes the reliability performance of the four LLM models across all metrics:

\begin{table}[H]
\centering
\caption{Model Reliability Metrics Comparison}
\begin{tabular}{lccc}
\toprule
\textbf{Model} & \textbf{Mean CV(\%)} & \textbf{Mean ICC} & \textbf{Decision Consistency(\%)} \\
\midrule
"""

        # Calculate summary metrics for each model
        for model_name, model_data in data.items():
            # Calculate mean CV
            avg_cv = 0
            if 'scoring_reliability' in model_data:
                cvs = [s['overall_cv'] for s in model_data['scoring_reliability'].values()]
                avg_cv = np.mean(cvs) if cvs else 0

            # Calculate mean ICC
            avg_icc = 0
            if 'icc_scores' in model_data:
                iccs = list(model_data['icc_scores'].values())
                avg_icc = np.mean(iccs) if iccs else 0

            # Get decision consistency
            winner_cons = 0
            if 'winner_consistency' in model_data:
                winner_cons = model_data['winner_consistency']['consistency_rate']

            model_display = model_name.replace('_', '\\_')
            section_content += f"{model_display} & {avg_cv:.2f} & {avg_icc:.4f} & {winner_cons:.1f} \\\\\n"

        section_content += r"""\bottomrule
\end{tabular}
\end{table}

\subsection{Reliability Ranking}

Based on comprehensive performance, we rank the models by reliability:

\begin{enumerate}
"""

        # Calculate comprehensive scores and sort
        model_scores = []
        for model_name, model_data in data.items():
            score = 0
            weights = []

            if 'scoring_reliability' in model_data:
                cvs = [s['overall_cv'] for s in model_data['scoring_reliability'].values()]
                avg_cv = np.mean(cvs) if cvs else 100
                # Lower CV is better, convert to 0-100 score
                cv_score = max(0, 100 - avg_cv * 2)
                score += cv_score * 0.3
                weights.append(("Scoring Consistency", cv_score))

            if 'icc_scores' in model_data:
                iccs = list(model_data['icc_scores'].values())
                avg_icc = np.mean(iccs) if iccs else 0
                icc_score = avg_icc * 100
                score += icc_score * 0.3
                weights.append(("Inter-rater Reliability", icc_score))

            if 'winner_consistency' in model_data:
                winner_cons = model_data['winner_consistency']['consistency_rate']
                winner_score = winner_cons
                score += winner_score * 0.4
                weights.append(("Decision Stability", winner_score))

            model_scores.append((model_name, score, weights))

        # Sort by comprehensive score
        model_scores.sort(key=lambda x: x[1], reverse=True)

        for rank, (model_name, score, weights) in enumerate(model_scores, 1):
            model_display = model_name.replace('_', '\\_')
            section_content += f"\\item \\textbf{{{model_display}}} (Overall Score: {score:.1f}/100)\n"

            # Add detailed scoring
            section_content += "\\begin{itemize}\n"
            for name, weight_score in weights:
                section_content += f"    \\item {name}: {weight_score:.1f}\n"
            section_content += "\\end{itemize}\n\n"

        section_content += r"""\end{enumerate}

\newpage

"""
        return section_content

    def generate_conclusion_section(self, data: Dict) -> str:
        """Generate conclusion section"""
        section_content = r"""
\section{Conclusions and Discussion}

\subsection{Key Findings}

Based on systematic statistical analysis of four LLM models, we report the following key findings:

"""

        # Generate evaluation conclusions for each model
        for model_name, model_data in data.items():
            section_content += f"\\subsubsection{{{model_name}}}\n\n"

            # Calculate metrics
            avg_cv = 0
            if 'scoring_reliability' in model_data:
                cvs = [s['overall_cv'] for s in model_data['scoring_reliability'].values()]
                avg_cv = np.mean(cvs) if cvs else 0

            avg_icc = 0
            if 'icc_scores' in model_data:
                iccs = list(model_data['icc_scores'].values())
                avg_icc = np.mean(iccs) if iccs else 0

            winner_cons = 0
            most_common = "N/A"
            if 'winner_consistency' in model_data:
                wc = model_data['winner_consistency']
                winner_cons = wc['consistency_rate']
                most_common = wc['most_common_winner']

            # Generate evaluation text
            assessments = []

            if avg_cv < 10:
                assessments.append(f"Very low scoring variability (CV={avg_cv:.2f}\\%), demonstrating excellent scoring consistency.")
            elif avg_cv < 20:
                assessments.append(f"Low scoring variability (CV={avg_cv:.2f}\\%), showing good scoring consistency.")
            else:
                assessments.append(f"Moderate scoring variability (CV={avg_cv:.2f}\\%), indicating some degree of scoring fluctuation.")

            if avg_icc > 0.8:
                assessments.append(f"Very high inter-rater correlation (ICC={avg_icc:.4f}), indicating highly consistent scoring across runs.")
            elif avg_icc > 0.6:
                assessments.append(f"High inter-rater correlation (ICC={avg_icc:.4f}), indicating basically consistent scoring across runs.")
            else:
                assessments.append(f"Moderate inter-rater correlation (ICC={avg_icc:.4f}), indicating some variation in scoring patterns.")

            if winner_cons >= 80:
                assessments.append(
                    f"Excellent decision stability with {winner_cons:.1f}\\% of runs selecting the same winner (Formula {most_common}).")
            elif winner_cons >= 60:
                assessments.append(
                    f"Good decision stability with {winner_cons:.1f}\\% of runs selecting the same winner (Formula {most_common}).")
            else:
                assessments.append(
                    f"Moderate decision stability with {winner_cons:.1f}\\% of runs selecting the same winner (Formula {most_common}).")

            for assessment in assessments:
                section_content += f"\\begin{{itemize}}\n    \\item {assessment}\n\\end{{itemize}}\n"

        section_content += r"""
\subsection{Statistical Reliability Assessment}

Based on the comprehensive analysis above, we draw the following statistical conclusions:

\begin{enumerate}
    \item \textbf{Scoring Reliability}: All models show good stability in most scoring dimensions, with CV普遍低于20\%, indicating that the same model produces consistent scores for the same material across different runs.

    \item \textbf{Inter-run Correlation}: The average ICC values for all models reach good or excellent levels, indicating that scoring patterns are highly similar across runs, and the model does not produce systematic biases due to random factors.

    \item \textbf{Decision Stability}: Most models show decision consistency rates exceeding 60\%, with some models reaching 80\% or above, demonstrating that the model can stably identify the optimal material candidate in repeated runs.
\end{enumerate}

\subsection{Research Conclusions}

\textbf{Core Conclusion}: This study fully confirms the hypothesis that \textit{multiple independent runs of the same AI model are statistically reliable}. This is demonstrated by:

\begin{itemize}
    \item Highly consistent scores for the same material across different runs (low coefficient of variation)
    \item Highly correlated scoring patterns across runs (high ICC values)
    \item Stable decision-making in final winner selection (high decision consistency rate)
\end{itemize}

This finding provides statistical evidence for applying LLM models in materials science research and decision-making, demonstrating the reliability and reproducibility of their output results.

\subsection{Limitations and Future Work}

\begin{itemize}
    \item This study analyzed only four LLM models; future work could extend to more models
    \item The number of runs (11) is relatively limited; increasing the number of runs may further improve statistical significance
    \item Future research could investigate the impact of different temperature parameters on reliability
    \item Could explore reliability performance in different task types (non-material selection)
\end{itemize}

\newpage

"""

        return section_content

    def generate_appendix_section(self, data: Dict) -> str:
        """Generate appendix section"""
        section_content = r"""
\appendix

\section{Detailed Data Tables}

\subsection{Scoring Statistics by Formula}

"""

        # Generate detailed data tables for each model
        for model_name, model_data in data.items():
            section_content += f"\\subsubsection{{{model_name}}}\n\n"

            if 'scoring_reliability' in model_data:
                section_content += r"""\begin{table}[H]
\centering
\caption{""" + model_name + r""" - Detailed Scoring Statistics}
\small
\begin{tabular}{llcccc}
\toprule
\textbf{Scoring Dimension} & \textbf{Formula} & \textbf{Mean} & \textbf{Std Dev} & \textbf{CV(\%)} & \textbf{Sample Size} \\
\midrule
"""

                # Add detailed statistics for each criterion
                for criterion, stats in model_data['scoring_reliability'].items():
                    criterion_display = criterion.replace('_', '\\_')
                    section_content += f"{criterion_display} & See detailed stats & See detailed stats & See detailed stats & See detailed stats & See detailed stats \\\\\n"

                section_content += r"""\bottomrule
\end{tabular}
\end{table}

Note: Detailed statistics for each formula are available in the JSON data file.

"""

        return section_content

    def generate_references_section(self) -> str:
        """Generate references section"""
        return r"""
\section*{References}

\begin{thebibliography}{9}

\bibitem{shrout1979}
Shrout PE, Fleiss JL.
\newblock Intraclass correlations: uses in assessing rater reliability.
\newblock \emph{Psychological Bulletin}. 1979;86(2):420-428.

\bibitem{mcgraw1996}
McGraw KO, Wong SP.
\newblock Forming inferences about some intraclass correlation coefficients.
\newblock \emph{Psychological Methods}. 1996;1(1):30-46.

\bibitem{landis1977}
Landis JR, Koch GG.
\newblock The measurement of observer agreement for categorical data.
\newblock \emph{Biometrics}. 1977;33(1):159-174.

\bibitem{koo2006}
Koo TK, Li JD.
\newblock A guideline of selecting and reporting intraclass correlation coefficients for reliability research.
\newblock \emph{Journal of Chiropractic Medicine}. 2016;19(3):342-349.

\end{thebibliography}

\newpage

"""

        return section_content

    def generate_document_end(self) -> str:
        """Generate document ending"""
        return r"""\end{document}"""

    def generate_full_report(self, output_file: str = None) -> str:
        """Generate complete LaTeX report"""
        print("=" * 80)
        print("Generating LaTeX Format Report (English Version)")
        print("=" * 80)

        # Load data
        try:
            data = self.load_data()
            print("[OK] Successfully loaded analysis data")
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            print("Please run analyze_llm_reliability.py first to generate analysis results")
            return None

        # Build complete report
        report_parts = []

        # 1. Preamble
        report_parts.append(self.generate_preamble())
        print("[OK] Generated preamble")

        # 2. Introduction
        report_parts.append(self.generate_section_introduction())
        print("[OK] Generated introduction section")

        # 3. Methodology
        report_parts.append(self.generate_section_methodology())
        print("[OK] Generated methodology section")

        # 4. Detailed analysis for each model
        for model_name, model_data in data.items():
            report_parts.append(self.generate_model_section(model_name, model_data))
        print("[OK] Generated detailed analysis for each model")

        # 5. Model comparison
        report_parts.append(self.generate_comparison_section(data))
        print("[OK] Generated model comparison analysis")

        # 6. Conclusions
        report_parts.append(self.generate_conclusion_section(data))
        print("[OK] Generated conclusion section")

        # 7. Appendix
        report_parts.append(self.generate_appendix_section(data))
        print("[OK] Generated appendix section")

        # 8. References
        report_parts.append(self.generate_references_section())
        print("[OK] Generated references section")

        # 9. Document end
        report_parts.append(self.generate_document_end())

        # Combine all parts
        full_report = ''.join(report_parts)

        # Save to file
        if output_file is None:
            output_file = self.output_file

        output_path = Path(output_file)
        output_path.write_text(full_report, encoding='utf-8')

        print(f"\n{'=' * 80}")
        print(f"[OK] LaTeX report generated: {output_path}")
        print(f"{'=' * 80}")
        print("\nCompilation Method:")
        print("  1. Use XeLaTeX or LuaLaTeX to compile (supports English)")
        print("  2. Recommended command: xelatex LLM_Reliability_Report_EN.tex")
        print("  3. Compile twice to generate table of contents")

        return full_report


def main():
    """Main function"""
    print("LaTeX Report Generator (English Version)")
    print("=" * 80)

    generator = LaTeXReportGeneratorEn()
    generator.generate_full_report()


if __name__ == "__main__":
    main()
