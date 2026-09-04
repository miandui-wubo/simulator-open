"""
测试脚本：设定一个实验值，跑通仿真调用流程（使用LAMMPS工作流接口的mock版本）

用法：
1) 建议先创建conda环境并安装依赖：
   conda create -n droplet-test python=3.10 -y
   conda activate droplet-test
   pip install -r requirements.txt

2) 运行本脚本：
   python examples/test_droplet_workflow.py

说明：
- 这里的 lammps_calculate / log_analyze 用mock函数模拟，不会真实调用LAMMPS
- 如果需要接入真实流程，替换 mock_runner / mock_parser 为您的实际函数
"""

import json
import numpy as np

from src.core.droplet_parameters import create_droplet_experiment_parameter_space
from src.core.objective import BaseObjective
from src.core.simulator_interface import LAMMPSWorkflowSimulator


# =============================================================================
# 实验观测值（示例）
# =============================================================================
EXPERIMENTAL_DATA = {
    "droplet_velocity": 0.05  # m/s
}


# =============================================================================
# Mock LAMMPS 工作流：runner 和 parser
# =============================================================================
def mock_runner(lammps_input: str) -> bool:
    """
    模拟 lammps_calculate(lammps_input)
    返回 True 表示“计算成功”
    """
    # 这里不做实际计算，只返回成功
    return True


def mock_parser(lammps_input: str):
    """
    模拟 log_analyze(lammps_input)
    将参数从 JSON 解析，并生成一个仿真结果
    """
    params = json.loads(lammps_input)

    # 简化的物理模型：速度随温差、接触角差、表面张力、粘度变化
    T_left = params["left_substrate_temperature"]
    T_right = params["right_substrate_temperature"]
    theta_left = params["left_contact_angle"]
    theta_right = params["right_contact_angle"]
    gamma = params["surface_tension"]
    mu = params["droplet_viscosity"]

    delta_T = abs(T_left - T_right)
    delta_theta = abs(theta_left - theta_right)

    # 简化速度模型（与 droplet_experiment 中的 mock 近似）
    d_gamma_dT = -0.0001
    temp_gradient = delta_T / 0.01
    marangoni_velocity = abs(d_gamma_dT * temp_gradient / max(mu, 1e-6)) * 0.001
    wetting_effect = gamma * np.sin(np.radians(delta_theta)) / max(mu, 1e-6)
    velocity = marangoni_velocity + 0.05 * np.sqrt(max(wetting_effect, 0))

    return {"droplet_velocity": velocity}


# =============================================================================
# 目标函数
# =============================================================================
class WorkflowObjective(BaseObjective):
    def __init__(self, simulator, experimental_data):
        super().__init__()
        self.simulator = simulator
        self.experimental_data = experimental_data

    def evaluate(self, params: np.ndarray) -> float:
        sim_results = self.simulator(params)

        total_error = 0.0
        for k, exp_val in self.experimental_data.items():
            if k not in sim_results:
                continue
            sim_val = sim_results[k]
            # 相对误差
            rel_err = abs(sim_val - exp_val) / (abs(exp_val) + 1e-12)
            total_error += rel_err
        return total_error


# =============================================================================
# 主流程：随机搜索演示
# =============================================================================
def main():
    print("=" * 70)
    print("测试：LAMMPS工作流（mock）参数→仿真→对比实验值")
    print("=" * 70)

    # 1) 创建参数空间
    param_space = create_droplet_experiment_parameter_space()

    # 2) 构造 LAMMPSWorkflowSimulator（使用mock runner/parser）
    simulator = LAMMPSWorkflowSimulator(
        work_dir=".",  # 此处不实际用到
        input_file="in.lammps",
        lammps_executable="lmp",
        runner=mock_runner,
        parser=mock_parser,
    )

    # 包装成可调用，便于 BaseObjective 使用
    def sim_call(param_array: np.ndarray):
        params_dict = param_space.array_to_dict(param_array)
        return simulator.run(params_dict)

    # 3) 创建目标函数
    objective = WorkflowObjective(simulator=sim_call, experimental_data=EXPERIMENTAL_DATA)

    # 4) 简单随机搜索演示
    n_trials = 5
    best_err = float("inf")
    best_params = None

    print("\n开始随机搜索 (示例，仅 5 次尝试)...")
    for i in range(n_trials):
        params = param_space.sample(1)[0]
        err = objective(params)
        if err < best_err:
            best_err = err
            best_params = params
        print(f"  试验 {i+1}/{n_trials}: 误差 = {err:.4f}")

    print("\n搜索结束。")
    print(f"最小误差: {best_err:.4f}")
    if best_params is not None:
        best_dict = param_space.array_to_dict(best_params)
        print("最优参数示例：")
        for k, v in best_dict.items():
            print(f"  {k}: {v:.4f}")


if __name__ == "__main__":
    main()


