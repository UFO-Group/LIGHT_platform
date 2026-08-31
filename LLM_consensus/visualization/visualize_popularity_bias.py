"""
流行性偏倚分析可视化模块

生成以下图表：
1. 材料频度分布柱状图
2. 每个模型的相关性热力图（7个维度）
3. 每个模型的原始vs去偏对比图
4. 每个模型的雷达图（6个维度，不含Total_Score）

关键原则：每个模型独立可视化
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PopularityBiasVisualizer:
    """流行性偏倚可视化器"""

    def __init__(self, base_dir: str = "."):
        """
        初始化可视化器

        Args:
            base_dir: 项目根目录
        """
        self.base_dir = base_dir
        self.output_dir = os.path.join(base_dir, "analysis", "popularity_bias_analysis")
        self.vis_dir = os.path.join(self.output_dir, "visualization")

        # 创建可视化目录
        os.makedirs(self.vis_dir, exist_ok=True)

        # 配方列表
        self.formulas = list(range(1, 11))
        self.formula_names = [f"Formula {i}" for i in self.formulas]

        # 评分维度（6个，不含Total_Score用于雷达图）
        self.dimensions = [
            "Mechanical_Safety", "Swelling_Performance", "Endothelialization",
            "SMC_inhibition", "Anti_inflammation", "Thrombogenicity"
        ]
        self.all_dimensions = self.dimensions + ["Total_Score"]

        # 模型名称映射
        self.model_names_map = {
            "gpt-5": "GPT-5",
            "grok-4": "Grok-4",
            "claude-opus-4-5-20251101": "Claude Opus 4.5",
            "gemini-3-pro-preview": "Gemini 3 Pro"
        }

        # 维度名称映射（用于显示）
        self.dimension_names_map = {
            "Mechanical_Safety": "Mechanical Safety",
            "Swelling_Performance": "Swelling Performance",
            "Endothelialization": "Endothelialization",
            "SMC_inhibition": "SMC Inhibition",
            "Anti_inflammation": "Anti-inflammation",
            "Thrombogenicity": "Thrombogenicity",
            "Total_Score": "Total Score"
        }

        # 设置绘图风格
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("husl")

    def load_material_frequencies(self) -> Dict[str, int]:
        """加载材料频度"""
        with open(os.path.join(self.output_dir, "material_frequencies.json"), 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_relative_frequencies(self) -> Dict[int, float]:
        """加载配方相对频度"""
        with open(os.path.join(self.output_dir, "relative_frequencies.json"), 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_correlation_results(self, model: str) -> Dict:
        """加载指定模型的相关性结果"""
        with open(os.path.join(self.output_dir, f"{model}_correlation_results.json"), 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_debiased_scores(self, model: str) -> pd.DataFrame:
        """加载指定模型的去偏后分数"""
        path = os.path.join(self.output_dir, f"{model}_debiased_scores.json")
        return pd.read_json(path)

    def plot_material_popularity_bar(self):
        """绘制材料频度分布柱状图"""
        material_freqs = self.load_material_frequencies()

        # 按频度排序
        sorted_materials = sorted(material_freqs.items(), key=lambda x: x[1], reverse=True)

        fig, ax = plt.subplots(figsize=(12, 6))

        materials = [m.replace('_', ' ').title() for m, _ in sorted_materials]
        freqs = [f for _, f in sorted_materials]

        bars = ax.barh(materials, freqs, color='steelblue', edgecolor='navy', alpha=0.7)

        # 添加数值标签
        for bar, freq in zip(bars, freqs):
            ax.text(freq, bar.get_y() + bar.get_height()/2, f'{freq:,}',
                   ha='left', va='center', fontsize=10, fontweight='bold')

        ax.set_xlabel('Frequency (0.5 × Datamuse + 0.5 × ArXiv)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Material', fontsize=12, fontweight='bold')
        ax.set_title('Material Popularity Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        output_path = os.path.join(self.vis_dir, "material_popularity_bar.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ 材料频度分布图已保存: {output_path}")

    def plot_correlation_heatmap(self, model: str):
        """
        绘制相关性热力图（每个模型独立）

        Args:
            model: 模型名称
        """
        corr_results = self.load_correlation_results(model)

        # 准备数据
        dimensions_display = [self.dimension_names_map[d] for d in self.all_dimensions]
        rho_values = [corr_results[d]["median_rho"] for d in self.all_dimensions]

        # 创建DataFrame（只包含相关系数）
        df = pd.DataFrame(rho_values, index=dimensions_display, columns=['Spearman ρ'])

        # 绘制热力图
        fig, ax = plt.subplots(figsize=(8, 6))

        # 使用颜色映射
        cmap = 'RdBu_r'
        vmin, vmax = -1, 1

        sns.heatmap(df, annot=True, fmt='.3f', cmap=cmap, vmin=vmin, vmax=vmax,
                   center=0, square=True, cbar_kws={'label': 'Spearman ρ'}, ax=ax)

        ax.set_title(f"Correlation Heatmap - {self.model_names_map.get(model, model)}\n"
                    f"Between Scores and Material Popularity",
                    fontsize=13, fontweight='bold', pad=15)

        # 添加边框标记
        for i, dimension in enumerate(self.all_dimensions):
            needs_debias = corr_results[dimension]["needs_debiasing"]
            for j in range(1):  # 只有一列
                if abs(rho_values[i]) > 0.6:
                    # 强相关：实线边框
                    rect = Rectangle((j, i), 1, 1, fill=False, edgecolor='red',
                                   linewidth=3, linestyle='-')
                    ax.add_patch(rect)
                elif abs(rho_values[i]) > 0.5:
                    # 中等相关：虚线边框
                    rect = Rectangle((j, i), 1, 1, fill=False, edgecolor='orange',
                                   linewidth=2, linestyle='--')
                    ax.add_patch(rect)

        # 添加图例
        legend_elements = [
            plt.Line2D([0], [0], color='red', lw=3, linestyle='-', label='Strong (|ρ|>0.6)'),
            plt.Line2D([0], [0], color='orange', lw=2, linestyle='--', label='Moderate (0.5<|ρ|≤0.6)')
        ]
        ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.15),
                 ncol=2, frameon=True)

        plt.tight_layout()

        model_name_safe = model.replace('/', '_')
        output_path = os.path.join(self.vis_dir, f"{model_name_safe}_correlation_heatmap.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ {model} 相关性热力图已保存: {output_path}")

    def plot_debias_comparison(self, model: str):
        """
        绘制原始vs去偏对比图（每个模型独立）

        Args:
            model: 模型名称
        """
        df = self.load_debiased_scores(model)
        corr_results = self.load_correlation_results(model)

        # 计算每个配方的平均分数
        avg_original = df.groupby('Formula')[self.all_dimensions].mean()

        # 获取去偏后的分数列
        debiased_cols = [f"{d}_debiased" for d in self.all_dimensions]
        avg_debiased = df.groupby('Formula')[debiased_cols].mean()

        # 绘制每个维度的对比图
        for i, dimension in enumerate(self.all_dimensions):
            fig, ax = plt.subplots(figsize=(12, 5))

            x = np.arange(len(self.formulas))
            width = 0.35

            original_vals = avg_original[dimension].values
            debiased_vals = avg_debiased[f"{dimension}_debiased"].values

            # 检查是否去偏
            needs_debias = corr_results[dimension]["needs_debiasing"]

            # 绘制柱状图
            bars1 = ax.bar(x - width/2, original_vals, width, label='Original',
                          color='steelblue', alpha=0.7, edgecolor='navy')
            bars2 = ax.bar(x + width/2, debiased_vals, width, label='Debiased',
                          color='coral', alpha=0.7, edgecolor='darkred')

            ax.set_xlabel('Formula', fontsize=12, fontweight='bold')
            ax.set_ylabel('Score (1-10)', fontsize=12, fontweight='bold')
            ax.set_title(f"{self.dimension_names_map[dimension]} - Original vs Debiasing\n"
                        f"{self.model_names_map.get(model, model)} "
                        f"{'(Debiased)' if needs_debias else '(No Debiasing)'}",
                        fontsize=13, fontweight='bold', pad=15)

            ax.set_xticks(x)
            ax.set_xticklabels(self.formula_names, rotation=45, ha='right')
            ax.set_ylim(0, 11)
            ax.legend(loc='upper right')
            ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()

            dimension_safe = dimension.replace('_', ' ')
            model_name_safe = model.replace('/', '_')
            output_path = os.path.join(self.vis_dir, f"{model_name_safe}_debias_comparison_{dimension_safe}.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"✓ {model} {dimension} 对比图已保存")

    def plot_radar_chart(self, model: str):
        """
        绘制雷达图（每个模型独立，6个维度不含Total_Score）

        Args:
            model: 模型名称
        """
        df = self.load_debiased_scores(model)
        corr_results = self.load_correlation_results(model)

        # 计算平均分数
        avg_original = df.groupby('Formula')[self.dimensions].mean()
        avg_debiased = df.groupby('Formula')[[f"{d}_debiased" for d in self.dimensions]].mean()

        # 计算全局平均（所有配方的平均）
        original_means = avg_original.mean().values
        debiased_means = avg_debiased.mean().values

        # 准备雷达图数据
        angles = np.linspace(0, 2 * np.pi, len(self.dimensions), endpoint=False).tolist()
        angles += angles[:1]  # 闭合

        original_means_radar = np.concatenate([original_means, [original_means[0]]])
        debiased_means_radar = np.concatenate([debiased_means, [debiased_means[0]]])

        dimension_labels = [self.dimension_names_map[d] for d in self.dimensions]

        # 绘制雷达图
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        # 绘制原始分数
        ax.plot(angles, original_means_radar, 'o-', linewidth=2, color='steelblue',
               label='Original', markersize=8)
        ax.fill(angles, original_means_radar, color='steelblue', alpha=0.25)

        # 绘制去偏分数
        ax.plot(angles, debiased_means_radar, 'o--', linewidth=2, color='coral',
               label='Debiased', markersize=8)
        ax.fill(angles, debiased_means_radar, color='coral', alpha=0.25)

        # 设置角度标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimension_labels, fontsize=11, fontweight='bold')

        # 设置y轴
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=9)
        ax.grid(True, alpha=0.3)

        # 标题和图例
        ax.set_title(f"Radar Chart - Original vs Debiasing\n{self.model_names_map.get(model, model)}",
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

        # 添加方向标签
        plt.tight_layout()

        model_name_safe = model.replace('/', '_')
        output_path = os.path.join(self.vis_dir, f"{model_name_safe}_radar_chart.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ {model} 雷达图已保存: {output_path}")

    def generate_all_visualizations(self, models: List[str]):
        """
        生成所有可视化（每个模型独立）

        Args:
            models: 要可视化的模型列表
        """
        print("\n" + "=" * 80)
        print("开始生成可视化")
        print("=" * 80)

        # 1. 材料频度分布图
        print("\n[1/2] 绘制材料频度分布图...")
        self.plot_material_popularity_bar()

        # 2. 每个模型的可视化
        print(f"\n[2/2] 为 {len(models)} 个模型生成可视化...")
        for model in models:
            print(f"\n处理模型: {model}")
            self.plot_correlation_heatmap(model)
            self.plot_debias_comparison(model)
            self.plot_radar_chart(model)

        print(f"\n{'=' * 80}")
        print(f"所有可视化已保存到: {self.vis_dir}")
        print(f"{'=' * 80}")

    def create_summary_report(self, models: List[str]):
        """
        创建分析摘要报告

        Args:
            models: 模型列表
        """
        material_freqs = self.load_material_frequencies()
        relative_freqs = self.load_relative_frequencies()

        report = []

        report.append("# 流行性偏倚分析摘要\n")
        report.append(f"分析日期: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        report.append("## 一、材料频度\n")
        for material, freq in sorted(material_freqs.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {material.replace('_', ' ')}: {freq:,}\n")

        report.append("\n## 二、配方相对频度（光环效应）\n")
        for formula_id in sorted(relative_freqs.keys()):
            report.append(f"- 配方 {formula_id}: {relative_freqs[formula_id]:.3f}\n")

        report.append("\n## 三、各模型相关性分析\n")
        for model in models:
            corr_results = self.load_correlation_results(model)
            report.append(f"\n### {self.model_names_map.get(model, model)}\n")

            strong = []
            moderate = []
            weak = []

            for dim, result in corr_results.items():
                rho = result["median_rho"]
                dim_name = self.dimension_names_map.get(dim, dim)

                if abs(rho) > 0.6:
                    strong.append(f"  - {dim_name}: ρ={rho:.3f} (强相关)\n")
                elif abs(rho) > 0.5:
                    moderate.append(f"  - {dim_name}: ρ={rho:.3f} (中等相关)\n")
                else:
                    weak.append(f"  - {dim_name}: ρ={rho:.3f} (弱/无相关)\n")

            if strong:
                report.append("**强相关维度（|ρ|>0.6）**\n")
                report.extend(strong)

            if moderate:
                report.append("**中等相关维度（0.5<|ρ|≤0.6）**\n")
                report.extend(moderate)

            if weak:
                report.append("**弱/无相关维度（|ρ|≤0.5）**\n")
                report.extend(weak)

        # 保存报告
        report_path = os.path.join(self.output_dir, "visualization", "summary.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(report)

        print(f"\n✓ 分析摘要报告已保存: {report_path}")


def main():
    """主函数"""
    visualizer = PopularityBiasVisualizer()

    # 获取需要可视化的模型
    output_dir = os.path.join(".", "analysis", "popularity_bias_analysis")
    models = []
    for filename in os.listdir(output_dir):
        if filename.endswith("_correlation_results.json"):
            model = filename.replace("_correlation_results.json", "")
            models.append(model)

    # 生成所有可视化
    visualizer.generate_all_visualizations(models)

    # 创建摘要报告
    visualizer.create_summary_report(models)


if __name__ == "__main__":
    main()
