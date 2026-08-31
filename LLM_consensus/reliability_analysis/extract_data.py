"""
LLM Consensus Data Extractor
从markdown文件中提取数据并规范化存储
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import io


class LLMDataExtractor:
    """从LLM输出文件中提取数据"""

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
        从文本中提取配方编号

        支持多种格式:
        - "Formula 5"
        - "Formula 5 (GelMA & PEG)"
        - "GelMA & PEG [Formula 5]"
        - "Formula 4: GelMA & Silk"

        参数:
            text: 包含配方信息的文本

        返回:
            配方编号(1-10)，如果未找到则返回None
        """
        # 尝试多种模式匹配
        patterns = [
            r'Formula\s*(\d+)',  # "Formula 5"
            r'\[Formula\s*(\d+)\]',  # "[Formula 5]"
            r'formula\s*(\d+)',  # "formula 5" (小写)
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
        从run头部提取run编号

        参数:
            run_header: run标题文本，如 "# Run 0 response"

        返回:
            run编号
        """
        match = re.search(r'Run\s*(\d+)', run_header, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return -1

    def extract_data_from_md(self, model_name: str) -> Optional[pd.DataFrame]:
        """
        从markdown文件中提取数据

        参数:
            model_name: 模型名称

        返回:
            包含提取数据的DataFrame，如果文件不存在或数据提取失败则返回None
        """
        file_path = self.base_dir / f"{model_name}.md"

        if not file_path.exists():
            print(f"警告: {file_path} 不存在")
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取每一轮的数据
        # 尝试多种分隔模式
        patterns = [
            r'# Run (\d+) response',  # 标准: "# Run 0 response"
            r'Run (\d+)',  # 简化: "Run 0"
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

            # 提取CSV数据
            csv_match = re.search(r'```csv\s*\n(.*?)```', run_content, re.DOTALL)
            if not csv_match:
                continue

            csv_text = csv_match.group(1)
            lines = [line.strip() for line in csv_text.split('\n') if line.strip()]

            if len(lines) < 2:
                continue

            # 解析CSV头部
            headers = [h.strip() for h in lines[0].split(',')]

            # 解析每一行数据
            for line in lines[1:]:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 8:
                    formula = parts[0]
                    # 提取Formula编号
                    formula_num = self.extract_formula_number(formula)
                    if formula_num is None:
                        continue

                    scores = {
                        'Model': model_name,
                        'Run': run_num,
                        'Formula': formula_num,
                        'Formula_Name': formula
                    }

                    # 提取各个评分
                    for j, criterion in enumerate(self.criteria):
                        if j + 1 < len(parts):
                            try:
                                scores[criterion] = float(parts[j + 1])
                            except ValueError:
                                scores[criterion] = np.nan

                    data_records.append(scores)

            # 提取获胜配方 - 尝试多种模式
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

            # 为本轮所有记录添加Winner字段
            for record in data_records:
                if record['Run'] == run_num:
                    record['Winner'] = winner_num

        if not data_records:
            return None

        df = pd.DataFrame(data_records)
        return df

    def extract_and_save_all(self) -> Dict[str, pd.DataFrame]:
        """
        提取所有模型的数据并保存

        返回:
            字典，键为模型名称，值为DataFrame
        """
        print("=" * 80)
        print("LLM数据提取器")
        print("=" * 80)

        all_data = {}

        for model in self.models:
            print(f"\n处理 {model}...")
            df = self.extract_data_from_md(model)
            if df is not None:
                all_data[model] = df
                print(f"  ✓ 成功提取 {len(df)} 条记录，{df['Run'].nunique()} 轮运行")

                # 检查Winner字段
                winner_counts = df[df['Winner'].notna()].groupby('Run')['Winner'].first()
                print(f"    - 提取到 {len(winner_counts)} 个获胜配方")

                # 检查缺失的Winner
                missing_winners = df['Run'].nunique() - len(winner_counts)
                if missing_winners > 0:
                    print(f"    ⚠ 警告: {missing_winners} 个run缺少获胜配方信息")
            else:
                print(f"  ✗ 提取失败")

        # 保存为JSON
        self.save_to_json(all_data)

        # 保存为CSV（每个模型单独一个文件）
        self.save_to_csv(all_data)

        print(f"\n总共提取了 {len(all_data)} 个模型的数据")
        return all_data

    def save_to_json(self, all_data: Dict[str, pd.DataFrame]) -> None:
        """保存为JSON格式"""
        output_path = self.base_dir / "extracted_data.json"

        export_data = {}
        for model, df in all_data.items():
            # 将DataFrame转换为字典列表，处理NaN值
            export_data[model] = df.to_dict('records')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=self.json_serializer)

        print(f"\n数据已保存到: {output_path}")

    @staticmethod
    def json_serializer(obj):
        """JSON序列化器，处理numpy和pandas类型"""
        if isinstance(obj, (np.integer, np.floating)):
            if np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def save_to_csv(self, all_data: Dict[str, pd.DataFrame]) -> None:
        """保存为CSV格式（每个模型一个文件）"""
        output_dir = self.base_dir / "extracted_csv"
        output_dir.mkdir(exist_ok=True)

        for model, df in all_data.items():
            output_path = output_dir / f"{model}.csv"
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"  CSV已保存: {output_path}")

        # 同时保存一个合并的CSV
        merged_df = pd.concat(all_data.values(), ignore_index=True)
        output_path = output_dir / "all_models.csv"
        merged_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"  合并CSV已保存: {output_path}")


def main():
    """主函数"""
    print("开始提取LLM数据...")

    extractor = LLMDataExtractor()
    all_data = extractor.extract_and_save_all()

    if all_data:
        print("\n" + "=" * 80)
        print("数据提取完成！")
        print("=" * 80)

        # 打印统计信息
        print("\n数据统计:")
        for model, df in all_data.items():
            print(f"\n{model}:")
            print(f"  总记录数: {len(df)}")
            print(f"  运行轮数: {df['Run'].nunique()}")
            print(f"  配方数: {df['Formula'].nunique()}")
            print(f"  有Winner的记录: {df['Winner'].notna().sum()}")
    else:
        print("\n错误: 未能提取任何数据")


if __name__ == "__main__":
    main()
