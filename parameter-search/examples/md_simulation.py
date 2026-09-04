"""分子动力学仿真参数拟合示例"""

import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.parameter_space import ParameterSpace, Parameter
from src.core.objective import SimulationObjective
from src.core.simulator_interface import MockSimulator, create_experimental_data
from src.optimizers.bayesian_optimizer import BayesianOptimizer
import matplotlib.pyplot as plt


def main():
    """
    模拟一个MD参数拟合场景
    
    场景：液态金属合金的扩散系数和粘度参数拟合
    """
    
    print("=" * 60)
    print("分子动力学仿真参数拟合示例")
    print("场景：液态金属合金性质预测")
    print("=" * 60)
    
    # 1. 定义参数空间（简化版，实际可能更多参数）
    print("\n步骤1: 定义力场参数空间")
    
    param_space = ParameterSpace([
        Parameter(
            name='epsilon',
            lower_bound=0.1,
            upper_bound=0.5,
            unit='eV',
            description='Lennard-Jones epsilon',
            physical_meaning='原子间相互作用强度'
        ),
        Parameter(
            name='sigma',
            lower_bound=2.5,
            upper_bound=3.5,
            unit='Å',
            description='Lennard-Jones sigma',
            physical_meaning='原子间平衡距离'
        ),
        Parameter(
            name='cutoff',
            lower_bound=8.0,
            upper_bound=12.0,
            unit='Å',
            description='Cutoff distance',
            physical_meaning='截断距离'
        ),
        Parameter(
            name='mass',
            lower_bound=50.0,
            upper_bound=70.0,
            unit='amu',
            description='Atomic mass',
            physical_meaning='原子质量'
        )
    ])
    
    print(f"{param_space}")
    
    # 2. 创建模拟仿真器
    print("\n步骤2: 初始化仿真器")
    
    simulator = MockSimulator(
        n_observables=3,  # 密度、扩散系数、粘度
        noise_level=0.03,
        computation_time=0.1  # 模拟每次仿真0.1秒
    )
    
    simulator.setup()
    print("  ✓ 仿真器已初始化")
    
    # 3. 生成"实验数据"（使用已知的"真实"参数）
    print("\n步骤3: 生成实验数据")
    
    true_params = {
        'epsilon': 0.32,
        'sigma': 3.0,
        'cutoff': 10.0,
        'mass': 60.0
    }
    
    print(f"  真实参数（实际应用中未知）:")
    for name, value in true_params.items():
        print(f"    {name}: {value}")
    
    experimental_data = create_experimental_data(
        simulator,
        true_params,
        n_measurements=3  # 3次重复测量求平均
    )
    
    print(f"\n  实验观测量:")
    for obs_name, obs_value in experimental_data.items():
        print(f"    {obs_name}: {obs_value}")
    
    # 4. 定义目标函数
    print("\n步骤4: 定义目标函数（仿真vs实验误差）")
    
    objective = SimulationObjective(
        simulator=simulator.run,
        experimental_data=experimental_data,
        observables=list(experimental_data.keys()),
        weights={
            'observable_0': 0.4,  # 密度权重
            'observable_1': 0.4,  # 扩散系数权重
            'observable_2': 0.2   # 粘度权重
        }
    )
    
    print("  目标: 最小化加权NRMSE")
    
    # 5. 运行贝叶斯优化（适合昂贵的仿真）
    print(f"\n{'='*60}")
    print("步骤5: 运行贝叶斯优化")
    print(f"{'='*60}")
    
    optimizer = BayesianOptimizer(
        param_space=param_space,
        objective=objective,
        n_initial_points=8,
        acquisition_func='EI'
    )
    
    best_params = optimizer.optimize(
        n_iterations=30,
        verbose=True
    )
    
    # 6. 分析结果
    print(f"\n{'='*60}")
    print("优化结果分析")
    print(f"{'='*60}")
    
    best_params_dict = param_space.array_to_dict(best_params)
    
    print(f"\n拟合结果:")
    print(f"{'参数':<15} {'真实值':<12} {'拟合值':<12} {'误差':<12}")
    print("-" * 51)
    
    for name in param_space.get_param_names():
        true_val = true_params[name]
        fitted_val = best_params_dict[name]
        error = abs(fitted_val - true_val) / true_val * 100
        print(f"{name:<15} {true_val:<12.4f} {fitted_val:<12.4f} {error:<12.2f}%")
    
    # 7. 验证拟合质量
    print(f"\n拟合质量验证:")
    
    fitted_observables = simulator.run(best_params_dict)
    
    print(f"{'观测量':<20} {'实验值':<15} {'仿真值':<15} {'相对误差':<15}")
    print("-" * 65)
    
    for obs_name in experimental_data.keys():
        exp_val = experimental_data[obs_name][0]
        sim_val = fitted_observables[obs_name][0]
        rel_error = abs(sim_val - exp_val) / abs(exp_val) * 100
        print(f"{obs_name:<20} {exp_val:<15.6f} {sim_val:<15.6f} {rel_error:<15.2f}%")
    
    print(f"\n最终误差函数值: {objective.best_value:.6f}")
    print(f"总仿真次数: {objective.n_evaluations}")
    
    # 8. 可视化收敛过程
    print(f"\n生成收敛曲线...")
    
    from src.utils.visualization import plot_convergence
    
    conv_data = optimizer.get_convergence_plot_data()
    fig, ax = plot_convergence(
        conv_data,
        title="MD参数拟合收敛曲线"
    )
    
    plt.savefig('md_fitting_convergence.png', dpi=300, bbox_inches='tight')
    print("收敛曲线已保存为 'md_fitting_convergence.png'")
    
    plt.show()
    
    # 清理
    simulator.cleanup()
    
    print(f"\n{'='*60}")
    print("MD参数拟合示例完成!")
    print(f"{'='*60}")
    
    print(f"\n关键要点:")
    print(f"  1. 贝叶斯优化非常适合昂贵的MD仿真")
    print(f"  2. 通过仅30次仿真实现了较好的参数拟合")
    print(f"  3. 可以权衡不同观测量的重要性")
    print(f"  4. 实际应用中可以连接真实的LAMMPS等MD软件")


if __name__ == "__main__":
    main()


