"""简单示例：使用不同优化器进行参数搜索"""

import numpy as np
import sys
import os

# 添加src到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.parameter_space import create_thermodynamic_parameter_space
from src.core.objective import MockObjective
from src.optimizers.bayesian_optimizer import BayesianOptimizer
from src.optimizers.genetic_algorithm import GeneticAlgorithm
from src.optimizers.pso_optimizer import ParticleSwarmOptimizer
from src.utils.visualization import plot_multi_optimizer_comparison, plot_convergence
import matplotlib.pyplot as plt


def main():
    """运行简单的参数搜索示例"""
    
    print("=" * 60)
    print("参数搜索示例：对比不同优化算法")
    print("=" * 60)
    
    # 1. 创建参数空间（10个热力学参数）
    param_space = create_thermodynamic_parameter_space()
    print(f"\n参数空间：\n{param_space}")
    
    # 2. 创建目标函数（模拟仿真vs实验的误差）
    objective = MockObjective(dimension=len(param_space), noise_level=0.01)
    print(f"\n目标：找到最小化误差的参数组合")
    print(f"真实参数（未知）存在于参数空间中")
    
    # 3. 测试不同优化器
    n_iterations = 50
    results = {}
    
    print(f"\n{'='*60}")
    print("测试 1: 贝叶斯优化")
    print(f"{'='*60}")
    
    objective_bo = MockObjective(dimension=len(param_space), noise_level=0.01)
    optimizer_bo = BayesianOptimizer(
        param_space=param_space,
        objective=objective_bo,
        n_initial_points=10
    )
    
    best_params_bo = optimizer_bo.optimize(n_iterations=n_iterations, verbose=True)
    results['Bayesian Optimization'] = optimizer_bo.get_convergence_plot_data()
    
    print(f"\n{'='*60}")
    print("测试 2: 遗传算法")
    print(f"{'='*60}")
    
    objective_ga = MockObjective(dimension=len(param_space), noise_level=0.01)
    optimizer_ga = GeneticAlgorithm(
        param_space=param_space,
        objective=objective_ga,
        population_size=30
    )
    
    best_params_ga = optimizer_ga.optimize(n_generations=n_iterations, verbose=True)
    results['Genetic Algorithm'] = optimizer_ga.get_convergence_data()
    
    print(f"\n{'='*60}")
    print("测试 3: 粒子群优化")
    print(f"{'='*60}")
    
    objective_pso = MockObjective(dimension=len(param_space), noise_level=0.01)
    optimizer_pso = ParticleSwarmOptimizer(
        param_space=param_space,
        objective=objective_pso,
        n_particles=30
    )
    
    best_params_pso = optimizer_pso.optimize(n_iterations=n_iterations, verbose=True)
    results['Particle Swarm'] = optimizer_pso.get_convergence_data()
    
    # 4. 对比结果
    print(f"\n{'='*60}")
    print("优化结果对比")
    print(f"{'='*60}")
    
    print(f"\n{'算法':<25} {'最优值':<15} {'评估次数':<15}")
    print("-" * 55)
    print(f"{'Bayesian Optimization':<25} {objective_bo.best_value:<15.6f} {objective_bo.n_evaluations:<15}")
    print(f"{'Genetic Algorithm':<25} {objective_ga.best_value:<15.6f} {objective_ga.n_evaluations:<15}")
    print(f"{'Particle Swarm':<25} {objective_pso.best_value:<15.6f} {objective_pso.n_evaluations:<15}")
    
    # 5. 可视化
    print(f"\n生成对比图...")
    
    fig, ax = plot_multi_optimizer_comparison(
        results,
        title="不同优化算法的收敛性能对比"
    )
    
    plt.savefig('optimizer_comparison.png', dpi=300, bbox_inches='tight')
    print("对比图已保存为 'optimizer_comparison.png'")
    
    # 显示图表
    plt.show()
    
    print(f"\n{'='*60}")
    print("示例完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()


