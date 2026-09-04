"""可视化工具"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Any
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sns.set_style("whitegrid")


def plot_convergence(
    data: Dict[str, np.ndarray],
    title: str = "优化收敛曲线",
    save_path: Optional[str] = None
):
    """
    绘制收敛曲线
    
    Args:
        data: 包含'iterations'和'values'的字典
        title: 图表标题
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    iterations = data.get('iterations', np.arange(len(data.get('values', []))))
    values = data.get('values', [])
    
    ax.plot(iterations, values, 'b-', linewidth=2, label='当前值')
    
    # 如果有累积最小值，也绘制出来
    if 'cumulative_min' in data:
        ax.plot(iterations, data['cumulative_min'], 'r-', linewidth=2, label='最优值')
    
    ax.set_xlabel('迭代次数', fontsize=12)
    ax.set_ylabel('目标函数值', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig, ax


def plot_multi_optimizer_comparison(
    results: Dict[str, Dict[str, np.ndarray]],
    title: str = "优化器性能对比",
    save_path: Optional[str] = None
):
    """
    对比多个优化器的性能
    
    Args:
        results: {optimizer_name: convergence_data}
        title: 标题
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
    
    for (name, data), color in zip(results.items(), colors):
        iterations = data.get('iterations', np.arange(len(data.get('best', []))))
        values = data.get('best', data.get('global_best', []))
        
        ax.plot(iterations, values, linewidth=2, label=name, color=color)
    
    ax.set_xlabel('迭代次数', fontsize=12)
    ax.set_ylabel('最优值', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')  # 对数尺度更容易看出差异
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig, ax


def plot_parameter_evolution(
    history: List[Dict[str, Any]],
    param_names: List[str],
    save_path: Optional[str] = None
):
    """
    绘制参数演化过程
    
    Args:
        history: 评估历史
        param_names: 参数名称列表
        save_path: 保存路径
    """
    n_params = len(param_names)
    
    fig, axes = plt.subplots(
        nrows=(n_params + 1) // 2,
        ncols=2,
        figsize=(14, 3 * ((n_params + 1) // 2))
    )
    
    axes = axes.flatten() if n_params > 1 else [axes]
    
    # 提取参数历史
    params_history = np.array([h['params'] for h in history])
    values_history = np.array([h['value'] for h in history])
    
    for i, (param_name, ax) in enumerate(zip(param_names, axes)):
        # 使用颜色表示目标函数值
        scatter = ax.scatter(
            range(len(params_history)),
            params_history[:, i],
            c=values_history,
            cmap='viridis',
            s=30,
            alpha=0.6
        )
        
        ax.set_xlabel('迭代次数', fontsize=10)
        ax.set_ylabel(param_name, fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.colorbar(scatter, ax=ax, label='目标函数值')
    
    # 隐藏多余的子图
    for ax in axes[n_params:]:
        ax.set_visible(False)
    
    plt.suptitle('参数演化过程', fontsize=14)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig, axes


def plot_2d_parameter_space(
    history: List[Dict[str, Any]],
    param_indices: tuple = (0, 1),
    param_names: Optional[List[str]] = None,
    contour_levels: int = 20,
    save_path: Optional[str] = None
):
    """
    绘制2D参数空间的搜索轨迹
    
    Args:
        history: 评估历史
        param_indices: 要显示的两个参数的索引
        param_names: 参数名称
        contour_levels: 等高线层数
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    params = np.array([h['params'] for h in history])
    values = np.array([h['value'] for h in history])
    
    i, j = param_indices
    
    # 绘制搜索轨迹
    scatter = ax.scatter(
        params[:, i],
        params[:, j],
        c=values,
        cmap='viridis',
        s=50,
        alpha=0.6,
        edgecolors='black',
        linewidth=0.5
    )
    
    # 绘制搜索路径
    ax.plot(params[:, i], params[:, j], 'r-', alpha=0.3, linewidth=1)
    
    # 标记起点和终点
    ax.scatter(params[0, i], params[0, j], c='green', s=200, marker='*', 
               edgecolors='black', linewidth=2, label='起点', zorder=10)
    ax.scatter(params[-1, i], params[-1, j], c='red', s=200, marker='*',
               edgecolors='black', linewidth=2, label='终点', zorder=10)
    
    # 标记最优点
    best_idx = np.argmin(values)
    ax.scatter(params[best_idx, i], params[best_idx, j], c='gold', s=300, 
               marker='*', edgecolors='black', linewidth=2, label='最优', zorder=11)
    
    plt.colorbar(scatter, ax=ax, label='目标函数值')
    
    if param_names:
        ax.set_xlabel(param_names[i], fontsize=12)
        ax.set_ylabel(param_names[j], fontsize=12)
    else:
        ax.set_xlabel(f'参数 {i}', fontsize=12)
        ax.set_ylabel(f'参数 {j}', fontsize=12)
    
    ax.set_title('参数空间搜索轨迹', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig, ax


def plot_multi_agent_diversity(
    data: Dict[str, np.ndarray],
    save_path: Optional[str] = None
):
    """
    绘制多智能体的多样性和收敛曲线
    
    Args:
        data: 包含'global_best'和'diversity'的字典
        save_path: 保存路径
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    iterations = data.get('iterations', np.arange(len(data.get('global_best', []))))
    
    # 绘制收敛曲线
    ax1.plot(iterations, data['global_best'], 'b-', linewidth=2)
    ax1.set_ylabel('全局最优值', fontsize=12)
    ax1.set_title('多智能体收敛曲线', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # 绘制多样性曲线
    ax2.plot(iterations, data['diversity'], 'r-', linewidth=2)
    ax2.set_xlabel('迭代次数', fontsize=12)
    ax2.set_ylabel('种群多样性', fontsize=12)
    ax2.set_title('智能体多样性演化', fontsize=14)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig, (ax1, ax2)


def plot_parallel_coordinates(
    history: List[Dict[str, Any]],
    param_names: List[str],
    n_best: int = 10,
    save_path: Optional[str] = None
):
    """
    绘制平行坐标图（适合高维参数可视化）
    
    Args:
        history: 评估历史
        param_names: 参数名称
        n_best: 显示最优的n个结果
        save_path: 保存路径
    """
    import pandas as pd
    from pandas.plotting import parallel_coordinates
    
    # 提取数据
    params = np.array([h['params'] for h in history])
    values = np.array([h['value'] for h in history])
    
    # 选择最优的n个
    best_indices = np.argsort(values)[:n_best]
    
    # 创建DataFrame
    df = pd.DataFrame(params[best_indices], columns=param_names)
    df['rank'] = range(1, n_best + 1)
    
    # 绘图
    fig, ax = plt.subplots(figsize=(14, 6))
    
    parallel_coordinates(
        df,
        'rank',
        colormap='viridis',
        ax=ax
    )
    
    ax.set_title(f'最优{n_best}个参数组合的平行坐标图', fontsize=14)
    ax.set_xlabel('参数', fontsize=12)
    ax.set_ylabel('归一化值', fontsize=12)
    ax.legend(title='排名', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig, ax


