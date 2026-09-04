"""多智能体协作搜索示例"""

import numpy as np
import sys
import os
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.parameter_space import create_thermodynamic_parameter_space
from src.core.objective import MockObjective
from src.agents.coordinator_agent import MultiAgentCoordinator
from src.utils.visualization import plot_multi_agent_diversity, plot_convergence


def main():
    """运行多智能体搜索示例"""
    
    print("=" * 60)
    print("多智能体协作参数搜索示例")
    print("=" * 60)
    
    # 1. 创建参数空间
    param_space = create_thermodynamic_parameter_space()
    print(f"\n参数空间维度: {len(param_space)}")
    
    # 2. 创建目标函数
    objective = MockObjective(dimension=len(param_space), noise_level=0.01)
    print(f"目标函数: MockObjective (模拟仿真vs实验误差)")
    
    # 3. 创建多智能体协调器
    print(f"\n初始化多智能体系统...")
    
    coordinator = MultiAgentCoordinator(
        param_space=param_space,
        objective=objective,
        n_explorers=5,   # 5个探索智能体
        n_exploiters=3,  # 3个利用智能体
        communication_interval=5  # 每5次迭代通信一次
    )
    
    print(f"  探索智能体: {len(coordinator.explorers)}")
    print(f"  利用智能体: {len(coordinator.exploiters)}")
    print(f"  通信间隔: {coordinator.communication_interval}")
    
    # 4. 运行搜索
    print(f"\n{'='*60}")
    print("开始多智能体搜索...")
    print(f"{'='*60}")
    
    best_params = coordinator.run(
        max_iterations=100,
        verbose=True
    )
    
    # 5. 分析结果
    print(f"\n{'='*60}")
    print("搜索结果分析")
    print(f"{'='*60}")
    
    # 智能体性能统计
    agent_stats = coordinator.get_agent_statistics()
    
    print(f"\n各智能体表现：")
    print(f"{'智能体ID':<20} {'角色':<15} {'最优值':<15} {'评估次数':<15}")
    print("-" * 65)
    
    for agent_id, stats in sorted(agent_stats.items(), key=lambda x: x[1]['best_value']):
        print(f"{agent_id:<20} {stats['role']:<15} {stats['best_value']:<15.6f} {stats['n_evaluations']:<15}")
    
    # 全局统计
    print(f"\n全局统计:")
    print(f"  总评估次数: {objective.n_evaluations}")
    print(f"  全局最优值: {coordinator.global_best_value:.6f}")
    print(f"  平均每智能体评估: {objective.n_evaluations / len(coordinator.all_agents):.1f}")
    
    # 6. 可视化
    print(f"\n生成可视化...")
    
    # 收敛和多样性曲线
    convergence_data = coordinator.get_convergence_data()
    
    fig1, axes = plot_multi_agent_diversity(
        convergence_data,
        save_path='multi_agent_convergence.png'
    )
    print("  多智能体收敛图已保存为 'multi_agent_convergence.png'")
    
    # 显示
    plt.show()
    
    print(f"\n{'='*60}")
    print("多智能体搜索完成!")
    print(f"{'='*60}")
    
    # 7. 显示最优参数
    print(f"\n最优参数组合:")
    for name, value in zip(param_space.get_param_names(), best_params):
        print(f"  {name}: {value:.6f}")


if __name__ == "__main__":
    main()


