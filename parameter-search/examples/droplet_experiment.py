"""
液滴实验参数搜索示例

目标：找到使仿真结果与实验结果一致的参数组合

场景说明：
- 输入：13个参数（温度、接触角、表面张力、密度、热容、导热系数等）
- 仿真：使用这些参数进行液滴运动仿真（可以是COMSOL、OpenFOAM或自定义代码）
- 实验数据：给定的实验观测值
- 目标：最小化仿真结果与实验结果的误差
"""

import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.droplet_parameters import (
    create_droplet_experiment_parameter_space,
    get_initial_guess_from_literature,
    print_parameter_summary,
    check_physical_constraints,
    REFERENCE_DATA
)
from src.core.objective import BaseObjective, SimulationObjective
from src.core.simulator_interface import LAMMPSWorkflowSimulator
from src.optimizers.bayesian_optimizer import BayesianOptimizer
from src.optimizers.pso_optimizer import ParticleSwarmOptimizer
from src.agents.coordinator_agent import MultiAgentCoordinator


# =============================================================================
# 1. 定义实验数据（这里需要您填入真实的实验结果）
# =============================================================================

# 示例实验数据 - 请替换为您的真实实验结果
EXPERIMENTAL_DATA = {
    # 液滴运动相关观测量
    'droplet_velocity': 0.05,       # m/s - 液滴迁移速度
    'migration_distance': 0.002,    # m - 一定时间内的迁移距离
    'final_position': 0.008,        # m - 最终位置
    'contact_angle_left_measured': 22.0,   # deg - 左侧实测接触角
    'contact_angle_right_measured': 18.0,  # deg - 右侧实测接触角
    
    # 温度场相关
    'temperature_gradient': 2.0,    # K/mm - 温度梯度
    
    # 时间相关
    'migration_time': 5.0,          # s - 迁移到目标位置的时间
}

# 各观测量的权重（根据测量精度和重要性设置）
OBSERVABLE_WEIGHTS = {
    'droplet_velocity': 0.25,
    'migration_distance': 0.25,
    'final_position': 0.20,
    'migration_time': 0.15,
    'contact_angle_left_measured': 0.075,
    'contact_angle_right_measured': 0.075,
}


# =============================================================================
# 2. 定义仿真函数接口
# =============================================================================

class DropletSimulator:
    """
    液滴仿真接口
    
    这是一个占位类，需要根据您的实际仿真软件进行实现
    可以连接：
    - COMSOL (通过LiveLink)
    - OpenFOAM
    - 自定义求解器
    - MATLAB/Python数值模拟
    """
    
    def __init__(
        self,
        simulation_type: str = 'mock',
        # LAMMPS工作流参数（可选）
        lammps_work_dir: str = "",
        lammps_input_file: str = "in.lammps",
        lammps_executable: str = "lmp",
        lammps_runner=None,   # lammps_calculate(lammps_input) -> bool
        lammps_parser=None,   # log_analyze(lammps_input) -> Dict[str, Any]
    ):
        """
        初始化仿真器
        
        Args:
            simulation_type: 'mock'(测试), 'comsol', 'openfoam', 'custom'
        """
        self.simulation_type = simulation_type
        self.lammps_work_dir = lammps_work_dir
        self.lammps_input_file = lammps_input_file
        self.lammps_executable = lammps_executable
        self.lammps_runner = lammps_runner
        self.lammps_parser = lammps_parser
        
    def run(self, params: dict) -> dict:
        """
        运行仿真
        
        Args:
            params: 13个参数的字典
            
        Returns:
            仿真结果字典，包含观测量
        """
        if self.simulation_type == 'mock':
            return self._run_mock_simulation(params)
        elif self.simulation_type == 'comsol':
            return self._run_comsol_simulation(params)
        elif self.simulation_type == 'lammps_workflow':
            return self._run_lammps_workflow(params)
        else:
            raise NotImplementedError(f"未实现的仿真类型: {self.simulation_type}")
    
    def _run_mock_simulation(self, params: dict) -> dict:
        """
        模拟仿真（用于测试优化流程）
        
        使用简化的物理模型生成结果
        """
        # 提取参数
        T_left = params['left_substrate_temperature']
        T_right = params['right_substrate_temperature']
        theta_left = params['left_contact_angle']
        theta_right = params['right_contact_angle']
        gamma = params['surface_tension']
        rho_droplet = params['droplet_density']
        mu = params['droplet_viscosity']
        k_left = params['left_thermal_conductivity']
        k_right = params['right_thermal_conductivity']
        
        # 简化物理模型（仅用于测试）
        # 实际应该是完整的CFD仿真
        
        # 温度梯度
        delta_T = abs(T_left - T_right)
        temp_gradient = delta_T / 0.01  # 假设基板长度10mm
        
        # Marangoni效应驱动速度（简化模型）
        # v ~ (dγ/dT) * (dT/dx) / μ
        d_gamma_dT = -0.0001  # N/(m·K) - 表面张力温度系数
        marangoni_velocity = abs(d_gamma_dT * temp_gradient / mu) * 0.001
        
        # 润湿性梯度效应
        delta_theta = abs(theta_left - theta_right)
        wetting_effect = gamma * np.sin(np.radians(delta_theta)) / (rho_droplet * 0.001)
        
        # 综合速度
        velocity = marangoni_velocity + 0.1 * np.sqrt(wetting_effect)
        
        # 添加噪声模拟实验误差
        noise = np.random.normal(0, 0.001)
        
        # 迁移距离和时间
        migration_time = 0.002 / (velocity + 1e-10)  # 迁移2mm
        migration_distance = velocity * 5.0  # 5秒内的距离
        
        return {
            'droplet_velocity': velocity + noise,
            'migration_distance': migration_distance,
            'final_position': 0.005 + migration_distance,
            'migration_time': min(migration_time, 10.0),
            'temperature_gradient': temp_gradient,
            'contact_angle_left_measured': theta_left + np.random.normal(0, 0.5),
            'contact_angle_right_measured': theta_right + np.random.normal(0, 0.5),
        }
    
    def _run_comsol_simulation(self, params: dict) -> dict:
        """
        通过COMSOL LiveLink运行仿真
        
        需要安装 COMSOL 和 mph (Python-COMSOL接口)
        """
        # TODO: 实现COMSOL接口
        # 示例代码框架：
        # 
        # import mph
        # client = mph.start()
        # model = client.load('droplet_model.mph')
        # 
        # # 设置参数
        # model.parameter('T_left', f'{params["left_substrate_temperature"]}[K]')
        # model.parameter('T_right', f'{params["right_substrate_temperature"]}[K]')
        # # ... 设置其他参数
        # 
        # # 运行求解
        # model.solve()
        # 
        # # 提取结果
        # velocity = model.evaluate('comp1.u')
        # ...
        #
        # return results
        
        raise NotImplementedError("请实现COMSOL接口")

    def _run_lammps_workflow(self, params: dict) -> dict:
        """
        按照 lammps_work/ fangzhendiaoyong.md 描述的流程：
        1) lammps_calculate(lammps_input) 运行仿真
        2) log_analyze(lammps_input) 解析结果
        3) 或直接 shell: cd work_dir && lmp -in in.lammps
        """
        if not self.lammps_work_dir:
            raise RuntimeError("未提供 lammps_work_dir，无法运行LAMMPS工作流")

        simulator = LAMMPSWorkflowSimulator(
            work_dir=self.lammps_work_dir,
            input_file=self.lammps_input_file,
            lammps_executable=self.lammps_executable,
            runner=self.lammps_runner,
            parser=self.lammps_parser,
        )
        return simulator.run(params)


# =============================================================================
# 3. 定义目标函数
# =============================================================================

class DropletObjective(BaseObjective):
    """
    液滴实验目标函数
    
    最小化仿真结果与实验数据的差异
    """
    
    def __init__(
        self,
        simulator: DropletSimulator,
        experimental_data: dict,
        weights: dict = None,
        param_space = None
    ):
        super().__init__()
        self.simulator = simulator
        self.experimental_data = experimental_data
        self.weights = weights or {k: 1.0 for k in experimental_data.keys()}
        self.param_space = param_space
        
        # 归一化权重
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
        
    def evaluate(self, params: np.ndarray) -> float:
        """
        评估参数
        
        Args:
            params: 13维参数数组
            
        Returns:
            归一化均方根误差 (越小越好)
        """
        # 将数组转换为字典
        if self.param_space is not None:
            params_dict = self.param_space.array_to_dict(params)
        else:
            # 如果没有param_space，使用默认顺序
            param_names = [
                'left_substrate_temperature', 'right_substrate_temperature',
                'left_contact_angle', 'right_contact_angle',
                'surface_tension',
                'left_substrate_density', 'right_substrate_density',
                'left_heat_capacity', 'right_heat_capacity',
                'droplet_density', 'droplet_viscosity',
                'left_thermal_conductivity', 'right_thermal_conductivity'
            ]
            params_dict = {name: params[i] for i, name in enumerate(param_names)}
        
        try:
            # 运行仿真
            sim_results = self.simulator.run(params_dict)
            
            # 计算加权NRMSE
            total_error = 0.0
            
            for obs_name, exp_value in self.experimental_data.items():
                if obs_name not in sim_results:
                    continue
                
                sim_value = sim_results[obs_name]
                weight = self.weights.get(obs_name, 0.0)
                
                # 相对误差
                if abs(exp_value) > 1e-10:
                    rel_error = abs(sim_value - exp_value) / abs(exp_value)
                else:
                    rel_error = abs(sim_value - exp_value)
                
                total_error += weight * rel_error
            
            return total_error
            
        except Exception as e:
            print(f"仿真失败: {e}")
            return 1e6  # 返回大惩罚值


# =============================================================================
# 4. 主程序
# =============================================================================

def main():
    """运行液滴实验参数搜索"""
    
    print("=" * 70)
    print("液滴实验参数搜索系统")
    print("目标：找到使仿真结果与实验结果一致的参数")
    print("=" * 70)
    
    # 1. 创建参数空间
    print("\n[步骤1] 创建参数空间")
    param_space = create_droplet_experiment_parameter_space()
    print_parameter_summary(param_space)
    
    # 2. 显示文献参考值
    print("\n[步骤2] 文献参考值")
    initial_guess = get_initial_guess_from_literature('GaInSn')
    print("基于GaInSn文献的初始猜测:")
    for name, value in initial_guess.items():
        print(f"  {name}: {value}")
    
    # 3. 创建仿真器
    print("\n[步骤3] 初始化仿真器")
    simulator = DropletSimulator(simulation_type='mock')
    print("  使用: Mock仿真器 (测试模式)")
    print("  实际应用时请替换为: COMSOL / OpenFOAM / 自定义求解器")
    # 如需调用 lammps_work/fangzhendiaoyong.md 描述的工作流，请改为：
    # from tools_lammps import lammps_calculate, log_analyze  # 用户自备脚本
    # simulator = DropletSimulator(
    #     simulation_type='lammps_workflow',
    #     lammps_work_dir="/path/to/lammps_work",  # 例如: /Users/xxx/lammps_work
    #     lammps_input_file="in.lammps",
    #     lammps_executable="lmp",
    #     lammps_runner=lammps_calculate,
    #     lammps_parser=log_analyze,
    # )
    
    # 4. 显示实验数据
    print("\n[步骤4] 实验数据")
    print("目标观测量:")
    for obs_name, obs_value in EXPERIMENTAL_DATA.items():
        weight = OBSERVABLE_WEIGHTS.get(obs_name, 0)
        print(f"  {obs_name}: {obs_value} (权重: {weight})")
    
    # 5. 创建目标函数
    print("\n[步骤5] 创建目标函数")
    objective = DropletObjective(
        simulator=simulator,
        experimental_data=EXPERIMENTAL_DATA,
        weights=OBSERVABLE_WEIGHTS,
        param_space=param_space
    )
    print("  目标: 最小化加权相对误差")
    
    # 6. 选择优化方法
    print("\n[步骤6] 选择优化方法")
    print("可选方法:")
    print("  1. 贝叶斯优化 (推荐，适合昂贵仿真)")
    print("  2. 粒子群优化 (快速)")
    print("  3. 多智能体搜索 (全面)")
    
    method = 1  # 默认使用贝叶斯优化
    
    # 7. 运行优化
    print(f"\n[步骤7] 开始参数搜索")
    print("-" * 70)
    
    if method == 1:
        print("使用贝叶斯优化...")
        optimizer = BayesianOptimizer(
            param_space=param_space,
            objective=objective,
            n_initial_points=15,  # 13个参数，初始点稍多一些
            acquisition_func='EI'
        )
        best_params = optimizer.optimize(n_iterations=50, verbose=True)
        
    elif method == 2:
        print("使用粒子群优化...")
        optimizer = ParticleSwarmOptimizer(
            param_space=param_space,
            objective=objective,
            n_particles=30
        )
        best_params = optimizer.optimize(n_iterations=100, verbose=True)
        
    elif method == 3:
        print("使用多智能体搜索...")
        coordinator = MultiAgentCoordinator(
            param_space=param_space,
            objective=objective,
            n_explorers=5,
            n_exploiters=3
        )
        best_params = coordinator.run(max_iterations=150, verbose=True)
    
    # 8. 结果分析
    print("\n" + "=" * 70)
    print("搜索结果")
    print("=" * 70)
    
    best_params_dict = param_space.array_to_dict(best_params)
    
    print("\n最优参数:")
    print("-" * 70)
    print(f"{'参数名称':<35} {'最优值':<15} {'单位':<10}")
    print("-" * 70)
    
    for p in param_space.parameters:
        value = best_params_dict[p.name]
        print(f"{p.physical_meaning:<35} {value:<15.4f} {p.unit:<10}")
    
    # 9. 验证结果
    print("\n验证最优参数:")
    print("-" * 70)
    
    sim_results = simulator.run(best_params_dict)
    
    print(f"{'观测量':<30} {'实验值':<15} {'仿真值':<15} {'相对误差':<15}")
    print("-" * 70)
    
    for obs_name in EXPERIMENTAL_DATA.keys():
        if obs_name in sim_results:
            exp_val = EXPERIMENTAL_DATA[obs_name]
            sim_val = sim_results[obs_name]
            rel_err = abs(sim_val - exp_val) / (abs(exp_val) + 1e-10) * 100
            print(f"{obs_name:<30} {exp_val:<15.4f} {sim_val:<15.4f} {rel_err:<15.2f}%")
    
    print("-" * 70)
    print(f"最终误差: {objective.best_value:.6f}")
    print(f"总评估次数: {objective.n_evaluations}")
    
    # 10. 物理约束检查
    print("\n物理约束检查:")
    check_result = check_physical_constraints(best_params_dict)
    if check_result['warnings']:
        print("警告:")
        for warning in check_result['warnings']:
            print(f"  ⚠️  {warning}")
    else:
        print("  ✓ 所有物理约束满足")
    
    print("\n" + "=" * 70)
    print("参数搜索完成!")
    print("=" * 70)
    
    return best_params_dict


if __name__ == "__main__":
    best_params = main()

