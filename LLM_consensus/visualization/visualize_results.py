"""
LLM可靠性分析可视化脚本
生成各种图表来展示分析结果
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional
import sys
import io

# 设置标准输出为UTF-8编码（解决Windows系统下的编码问题）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置英文字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 设置seaborn样式
sns.set_style("whitegrid")
sns.set_palette("husl")


class LLMResultVisualizer:
    """LLM可靠性分析结果可视化"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.data_file = self.base_dir / "reliability_analysis_results.json"
        self.output_dir = self.base_dir / "visualizations"
        self.output_dir.mkdir(exist_ok=True)

        # 颜色方案
        self.model_colors = {
            'gpt-5': '#FF6B6B',
            'grok-4': '#4ECDC4',
            'claude-opus-4-5-20251101': '#45B7D1',
            'gemini-3-pro-preview': '#FFA07A'
        }

    def load_data(self) -> Dict:
        """加载分析结果数据"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    def plot_overall_comparison(self, data: Dict, save: bool = True) -> None:
        """绘制整体对比图 - 雷达图"""
        # 准备数据
        models = list(data.keys())
        metrics = ['平均CV', '平均ICC', '决策一致性']

        model_scores = {}
        for model in models:
            # 计算平均CV
            avg_cv = np.mean([s['overall_cv'] for s in data[model]['scoring_reliability'].values()])

            # 计算平均ICC
            avg_icc = np.mean(list(data[model]['icc_scores'].values()))

            # 决策一致性
            winner_cons = data[model]['winner_consistency']['consistency_rate']

            model_scores[model] = {
                '平均CV': 100 - avg_cv,  # CV越低越好，转换为分数
                '平均ICC': avg_icc * 100,  # ICC转换为百分制
                '决策一致性': winner_cons
            }

        # 创建雷达图
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]

        # 绘制每个模型
        for model in models:
            values = [model_scores[model][metric] for metric in metrics]
            values += values[:1]

            ax.plot(angles, values, 'o-', linewidth=2,
                   label=model, color=self.model_colors[model])
            ax.fill(angles, values, alpha=0.15, color=self.model_colors[model])

        # 设置标签和网格
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics, fontsize=12)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)

        # 标题和图例
        plt.title('LLM模型可靠性综合对比\n(数值越高表示越可靠)',
                 fontsize=14, fontweight='bold', pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'overall_comparison_radar.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: overall_comparison_radar.png")

        plt.close()

    def plot_cv_comparison(self, data: Dict, save: bool = True) -> None:
        """绘制CV对比柱状图"""
        # 准备数据
        models = list(data.keys())
        criteria = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
                   'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']

        cv_data = []
        for model in models:
            for criterion in criteria:
                if criterion in data[model]['scoring_reliability']:
                    cv_data.append({
                        'Model': model,
                        'Criterion': criterion.replace('_', '\n'),
                        'CV': data[model]['scoring_reliability'][criterion]['overall_cv']
                    })

        df = pd.DataFrame(cv_data)

        # 创建分组柱状图
        fig, ax = plt.subplots(figsize=(14, 6))

        models_list = list(df['Model'].unique())
        x = np.arange(len(criteria))
        width = 0.2

        for i, model in enumerate(models_list):
            model_data = df[df['Model'] == model]['CV'].values
            ax.bar(x + i * width, model_data, width,
                   label=model, color=self.model_colors[model], alpha=0.8)

        # 添加参考线
        ax.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='优秀 (CV<10%)')
        ax.axhline(y=20, color='orange', linestyle='--', alpha=0.5, label='一般 (CV≥20%)')

        ax.set_xlabel('评分维度', fontsize=12, fontweight='bold')
        ax.set_ylabel('变异系数 CV (%)', fontsize=12, fontweight='bold')
        ax.set_title('各模型在不同评分维度的变异系数对比\n(越低越好)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(criteria, rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'cv_comparison.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: cv_comparison.png")

        plt.close()

    def plot_icc_comparison(self, data: Dict, save: bool = True) -> None:
        """绘制ICC对比热图"""
        # 准备数据
        models = list(data.keys())
        criteria = ['Mechanical_Safety', 'Swelling_Performance', 'Endothelialization',
                   'SMC_inhibition', 'Anti_inflammation', 'Thrombogenicity', 'Total_Score']

        # 创建ICC矩阵
        icc_matrix = pd.DataFrame(index=criteria, columns=models)

        for model in models:
            for criterion in criteria:
                if criterion in data[model]['icc_scores']:
                    icc_matrix.loc[criterion, model] = data[model]['icc_scores'][criterion]

        icc_matrix = icc_matrix.astype(float)

        # 绘制热图
        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(icc_matrix, annot=True, fmt='.4f', cmap='RdYlGn',
                   vmin=0, vmax=1, cbar_kws={'label': 'ICC值'},
                   linewidths=0.5, linecolor='white', ax=ax)

        ax.set_title('组内相关系数(ICC)热图\n(数值越高表示一致性越好)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('模型', fontsize=12, fontweight='bold')
        ax.set_ylabel('评分维度', fontsize=12, fontweight='bold')

        # 旋转标签
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'icc_heatmap.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: icc_heatmap.png")

        plt.close()

    def plot_winner_consistency(self, data: Dict, save: bool = True) -> None:
        """绘制决策一致性对比图"""
        # 准备数据
        models = list(data.keys())

        consistency_data = []
        for model in models:
            wc = data[model]['winner_consistency']
            if 'error' not in wc:
                consistency_data.append({
                    'Model': model,
                    '一致性率 (%)': wc['consistency_rate'],
                    '最常见配方': f"Formula {int(wc['most_common_winner'])}",
                    '出现次数': int(wc['most_common_count'])
                })

        df = pd.DataFrame(consistency_data)

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 左图: 一致性率柱状图
        colors = [self.model_colors[model] for model in df['Model']]
        bars = ax1.bar(df['Model'], df['一致性率 (%)'], color=colors, alpha=0.8, edgecolor='black')

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # 添加参考线
        ax1.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='优秀 (≥80%)')
        ax1.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='良好 (≥60%)')

        ax1.set_xlabel('模型', fontsize=12, fontweight='bold')
        ax1.set_ylabel('决策一致性率 (%)', fontsize=12, fontweight='bold')
        ax1.set_title('各模型决策一致性率对比', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim(0, 105)

        # 右图: 获胜配方分布堆叠柱状图
        all_formulas = set()
        for model in models:
            wc = data[model]['winner_consistency']
            if 'error' not in wc and 'winner_distribution' in wc:
                dist = wc['winner_distribution']
                formulas = sorted(dist.keys())
                all_formulas.update(formulas)
                counts = [dist[f] for f in formulas]

                # 使用偏移量避免重叠
                offset = list(models).index(model) * 0.15
                x_pos = np.arange(len(formulas)) + offset

                ax2.bar(x_pos, counts, width=0.15, label=model,
                       color=self.model_colors[model], alpha=0.8)

        ax2.set_xlabel('获胜配方', fontsize=12, fontweight='bold')
        ax2.set_ylabel('出现次数', fontsize=12, fontweight='bold')
        ax2.set_title('获胜配方分布', fontsize=12, fontweight='bold')

        if all_formulas:
            formulas_sorted = sorted(all_formulas)
            ax2.set_xticks(np.arange(len(formulas_sorted)) + 0.225)
            ax2.set_xticklabels([f'F{f}' for f in formulas_sorted])
        ax2.legend(fontsize=9, loc='upper right')
        ax2.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'winner_consistency.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: winner_consistency.png")

        plt.close()

    def plot_reliability_ranking(self, data: Dict, save: bool = True) -> None:
        """绘制可靠性排名图"""
        # 计算综合得分
        models = list(data.keys())
        scores = []

        for model in models:
            # CV得分 (越低越好，转换为分数)
            avg_cv = np.mean([s['overall_cv'] for s in data[model]['scoring_reliability'].values()])
            cv_score = max(0, 100 - avg_cv * 2)

            # ICC得分
            avg_icc = np.mean(list(data[model]['icc_scores'].values()))
            icc_score = avg_icc * 100

            # 决策一致性得分
            winner_cons = data[model]['winner_consistency']['consistency_rate']

            # 综合得分 (加权平均)
            overall_score = cv_score * 0.3 + icc_score * 0.3 + winner_cons * 0.4

            scores.append({
                'Model': model,
                '评分一致性': cv_score,
                '组内相关性': icc_score,
                '决策稳定性': winner_cons,
                '综合得分': overall_score
            })

        df = pd.DataFrame(scores).sort_values('综合得分', ascending=True)

        # 创建水平条形图
        fig, ax = plt.subplots(figsize=(10, 6))

        y_pos = np.arange(len(df))
        colors = [self.model_colors[model] for model in df['Model']]

        ax.barh(y_pos, df['综合得分'], color=colors, alpha=0.8, edgecolor='black')

        # 添加数值标签
        for i, (idx, row) in enumerate(df.iterrows()):
            ax.text(row['综合得分'] + 1, i, f"{row['综合得分']:.1f}",
                   va='center', fontsize=10, fontweight='bold')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['Model'], fontsize=11)
        ax.set_xlabel('综合得分', fontsize=12, fontweight='bold')
        ax.set_title('LLM模型可靠性排名\n(基于评分一致性、组内相关性和决策稳定性的加权平均)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlim(0, 100)
        ax.grid(axis='x', alpha=0.3)

        # 添加图例
        legend_text = '评分权重:\n• 评分一致性: 30%\n• 组内相关性: 30%\n• 决策稳定性: 40%'
        ax.text(0.98, 0.5, legend_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='center', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'reliability_ranking.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: reliability_ranking.png")

        plt.close()

    def plot_model_detail(self, data: Dict, model_name: str, save: bool = True) -> None:
        """绘制单个模型的详细分析图"""
        if model_name not in data:
            print(f"✗ 模型 {model_name} 不存在")
            return

        model_data = data[model_name]

        # 创建子图
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

        # 1. CV雷达图
        ax1 = fig.add_subplot(gs[0, 0])
        criteria = list(model_data['scoring_reliability'].keys())
        cv_values = [model_data['scoring_reliability'][c]['overall_cv'] for c in criteria]

        angles = np.linspace(0, 2 * np.pi, len(criteria), endpoint=False)
        cv_values += cv_values[:1]
        angles += angles[:1]

        ax1.plot(angles, cv_values, 'o-', linewidth=2, color=self.model_colors[model_name])
        ax1.fill(angles, cv_values, alpha=0.25, color=self.model_colors[model_name])
        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels([c.replace('_', '\n') for c in criteria], fontsize=8)
        ax1.set_ylim(0, max(cv_values) * 1.1)
        ax1.set_title('评分变异系数', fontweight='bold', fontsize=11)
        ax1.grid(True)

        # 2. ICC柱状图
        ax2 = fig.add_subplot(gs[0, 1])
        icc_criteria = list(model_data['icc_scores'].keys())
        icc_values = [model_data['icc_scores'][c] for c in icc_criteria]

        colors_icc = ['green' if v > 0.8 else 'orange' if v > 0.6 else 'red' for v in icc_values]
        ax2.barh(range(len(icc_criteria)), icc_values, color=colors_icc, alpha=0.7, edgecolor='black')
        ax2.set_yticks(range(len(icc_criteria)))
        ax2.set_yticklabels([c.replace('_', '\n') for c in icc_criteria], fontsize=8)
        ax2.set_xlabel('ICC值', fontsize=10)
        ax2.set_title('组内相关系数', fontweight='bold', fontsize=11)
        ax2.set_xlim(0, 1)
        ax2.axvline(x=0.8, color='green', linestyle='--', alpha=0.5, label='优秀')
        ax2.axvline(x=0.6, color='orange', linestyle='--', alpha=0.5, label='良好')
        ax2.legend(fontsize=8)
        ax2.grid(axis='x', alpha=0.3)

        # 3. 获胜配方分布饼图
        ax3 = fig.add_subplot(gs[0, 2])
        wc = model_data['winner_consistency']
        if 'error' not in wc and 'winner_distribution' in wc:
            dist = wc['winner_distribution']
            formulas = sorted(dist.keys())
            sizes = [dist[f] for f in formulas]
            labels = [f'Formula {f}' for f in formulas]

            colors_pie = plt.cm.Set3(np.linspace(0, 1, len(formulas)))
            wedges, texts, autotexts = ax3.pie(sizes, labels=labels, autopct='%1.1f%%',
                                             colors=colors_pie, startangle=90)
            ax3.set_title(f'获胜配方分布\n(一致性率: {wc["consistency_rate"]:.1f}%)',
                         fontweight='bold', fontsize=11)

        # 4. 评分范围箱线图
        ax4 = fig.add_subplot(gs[1, :])

        # 准备数据: 每个评分维度在11轮中的值
        criterion_data = {}
        for criterion in criteria:
            criterion_data[criterion] = []

        # 注意: 这里需要原始数据，我们从JSON中无法直接获取
        # 所以我们显示统计摘要
        summary_data = []
        for criterion in criteria:
            stats = model_data['scoring_reliability'][criterion]
            summary_data.append({
                'Criterion': criterion.replace('_', '\n'),
                'Mean': stats['overall_cv'],
                'Max': stats['max_cv'],
                'Min': stats['min_cv']
            })

        df_summary = pd.DataFrame(summary_data)
        x = np.arange(len(criteria))
        width = 0.25

        ax4.bar(x - width, df_summary['Min'], width, label='最小CV', color='lightblue', alpha=0.7)
        ax4.bar(x, df_summary['Mean'], width, label='平均CV', color=self.model_colors[model_name], alpha=0.7)
        ax4.bar(x + width, df_summary['Max'], width, label='最大CV', color='lightcoral', alpha=0.7)

        ax4.set_xlabel('评分维度', fontsize=11, fontweight='bold')
        ax4.set_ylabel('变异系数 (%)', fontsize=11, fontweight='bold')
        ax4.set_title('评分变异系数统计', fontweight='bold', fontsize=12)
        ax4.set_xticks(x)
        ax4.set_xticklabels(df_summary['Criterion'], rotation=45, ha='right')
        ax4.legend(fontsize=10)
        ax4.grid(axis='y', alpha=0.3)

        # 总标题
        fig.suptitle(f'{model_name} - 详细可靠性分析',
                    fontsize=16, fontweight='bold', y=0.995)

        if save:
            plt.savefig(self.output_dir / f'{model_name}_detail.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: {model_name}_detail.png")

        plt.close()

    def plot_entropy_analysis(self, data: Dict, save: bool = True) -> None:
        """绘制熵分析图"""
        models = list(data.keys())

        entropy_data = []
        for model in models:
            wc = data[model]['winner_consistency']
            if 'error' not in wc:
                entropy_data.append({
                    'Model': model,
                    '实际熵': wc['entropy'],
                    '最大熵': wc['max_entropy'],
                    '一致性率': wc['consistency_rate']
                })

        df = pd.DataFrame(entropy_data)

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 左图: 熵值对比
        x = np.arange(len(df))
        width = 0.35

        bars1 = ax1.bar(x - width/2, df['实际熵'], width, label='实际熵',
                       color='steelblue', alpha=0.8)
        bars2 = ax1.bar(x + width/2, df['最大熵'], width, label='最大熵',
                       color='lightgray', alpha=0.8)

        ax1.set_xlabel('模型', fontsize=12, fontweight='bold')
        ax1.set_ylabel('熵值', fontsize=12, fontweight='bold')
        ax1.set_title('信息熵对比\n(越低表示决策越集中)',
                     fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(df['Model'], rotation=45, ha='right')
        ax1.legend(fontsize=10)
        ax1.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=8)

        # 右图: 一致性率 vs 熵值散点图
        for i, row in df.iterrows():
            ax2.scatter(row['实际熵'], row['一致性率'],
                      s=200, color=self.model_colors[row['Model']],
                      alpha=0.7, edgecolor='black', label=row['Model'])
            ax2.annotate(row['Model'], (row['实际熵'], row['一致性率']),
                       fontsize=9, xytext=(5, 5), textcoords='offset points')

        ax2.set_xlabel('信息熵', fontsize=12, fontweight='bold')
        ax2.set_ylabel('决策一致性率 (%)', fontsize=12, fontweight='bold')
        ax2.set_title('熵值与一致性的关系\n(熵越低，一致性越高)',
                     fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # 添加趋势线
        z = np.polyfit(df['实际熵'], df['一致性率'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(df['实际熵'].min(), df['实际熵'].max(), 100)
        ax2.plot(x_trend, p(x_trend), "r--", alpha=0.5, linewidth=2, label='趋势线')
        ax2.legend(fontsize=9)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'entropy_analysis.png',
                       dpi=300, bbox_inches='tight')
            print(f"✓ 已保存: entropy_analysis.png")

        plt.close()

    def generate_all_visualizations(self, show: bool = False) -> None:
        """生成所有可视化图表"""
        print("=" * 80)
        print("LLM可靠性分析 - 可视化生成")
        print("=" * 80)

        # 加载数据
        try:
            data = self.load_data()
            print(f"\n✓ 成功加载分析数据")
        except FileNotFoundError as e:
            print(f"\n✗ 错误: {e}")
            print("请先运行 analyze_llm_reliability.py 生成分析结果")
            return

        print(f"\n开始生成可视化图表...")
        print(f"输出目录: {self.output_dir}")
        print("-" * 80)

        # 生成各种图表
        self.plot_overall_comparison(data)
        self.plot_cv_comparison(data)
        self.plot_icc_comparison(data)
        self.plot_winner_consistency(data)
        self.plot_reliability_ranking(data)
        self.plot_entropy_analysis(data)

        # 为每个模型生成详细图
        print("-" * 80)
        print("\n生成各模型详细分析图:")
        for model in data.keys():
            self.plot_model_detail(data, model)

        print("-" * 80)
        print(f"\n✓ 所有图表已生成！共 {len(list(self.output_dir.glob('*.png')))} 个文件")
        print(f"✓ 保存位置: {self.output_dir}")

        # 显示图表统计
        png_files = list(self.output_dir.glob('*.png'))
        total_size = sum(f.stat().st_size for f in png_files) / 1024  # KB

        print(f"\n文件统计:")
        print(f"  文件数量: {len(png_files)}")
        print(f"  总大小: {total_size:.1f} KB")
        print(f"  平均大小: {total_size/len(png_files):.1f} KB")

        print("\n" + "=" * 80)
        print("可视化完成！")
        print("=" * 80)

        if show:
            print("\n正在显示图表...")
            import os
            for img_file in sorted(self.output_dir.glob('*.png')):
                os.startfile(str(img_file))


def main():
    """主函数"""
    visualizer = LLMResultVisualizer()
    visualizer.generate_all_visualizations(show=False)


if __name__ == "__main__":
    main()
