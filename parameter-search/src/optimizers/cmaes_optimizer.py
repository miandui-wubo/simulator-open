"""CMA-ES 优化器 — 针对昂贵中等维度黑盒优化的最佳选择

协方差矩阵自适应进化策略 (CMA-ES) 是一种无梯度优化算法，
通过自适应学习参数间的协方差结构来高效搜索。

为什么 CMA-ES 最适合本项目（COMSOL 接触角参数搜索）：
1. 维度匹配：13 维参数空间正好在 CMA-ES 的最佳区间（5-100 维）
2. 昂贵评估：每次 COMSOL 仿真耗时数分钟，CMA-ES 的样本效率远优于 GA/PSO
3. 参数耦合：表面张力、黏度、温度之间存在物理耦合，
   CMA-ES 通过协方差矩阵自动捕捉这些耦合关系
4. 无需调参：CMA-ES 的超参数几乎全部自适应，不需要手动调节
"""

import numpy as np
from typing import Optional, Callable, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective


class CMAESOptimizer:
    """
    CMA-ES (协方差矩阵自适应进化策略) 优化器

    核心优势：
    - 自动学习参数间的相关性（通过协方差矩阵）
    - 步长自适应（sigma 自动调整）
    - 对初始点不敏感
    - 在 5-100 维连续优化中通常是最优选择
    - 不需要手动调节超参数
    """

    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        sigma0: Optional[float] = None,
        population_size: Optional[int] = None,
        random_state: Optional[int] = None,
    ):
        """
        Args:
            param_space: 参数空间
            objective: 目标函数
            sigma0: 初始步长（搜索范围的比例）。None 时自动设为搜索范围的 1/3。
            population_size: 种群大小。None 时使用 CMA-ES 默认值（约 4+3*ln(dim)）。
            random_state: 随机种子
        """
        self.param_space = param_space
        self.objective = objective
        self.dim = len(param_space)

        bounds = np.array(param_space.get_bounds())
        self.lower = bounds[:, 0]
        self.upper = bounds[:, 1]
        self.ranges = self.upper - self.lower

        if sigma0 is None:
            sigma0 = np.mean(self.ranges) / 3.0
        self.sigma0 = sigma0

        self.population_size = population_size
        self.random_state = random_state

        self.result = None
        self.history = {"best": [], "mean": [], "sigma": []}

    def optimize(
        self,
        n_iterations: int = 50,
        verbose: bool = True,
        callback: Optional[Callable] = None,
    ) -> np.ndarray:
        """
        执行 CMA-ES 优化

        Args:
            n_iterations: 最大迭代次数（以代计，每代评估 population_size 个点）
            verbose: 是否打印进度
            callback: 每代结束后的回调 callback(best_params, best_value)

        Returns:
            最优参数 (np.ndarray)
        """
        import cma

        x0 = (self.lower + self.upper) / 2.0

        opts = {
            "bounds": [self.lower.tolist(), self.upper.tolist()],
            "maxiter": n_iterations,
            "verbose": -9 if not verbose else 1,
            "CMA_stds": (self.ranges / (2.0 * self.sigma0)).tolist(),
        }

        if self.population_size is not None:
            opts["popsize"] = self.population_size
        if self.random_state is not None:
            opts["seed"] = self.random_state

        es = cma.CMAEvolutionStrategy(x0.tolist(), self.sigma0, opts)

        generation = 0
        while not es.stop():
            solutions = es.ask()

            fitnesses = []
            for x in solutions:
                x_arr = np.array(x)
                x_arr = self.param_space.clip(x_arr)
                val = self.objective(x_arr)
                fitnesses.append(val)

            es.tell(solutions, fitnesses)

            best_val = min(fitnesses)
            mean_val = np.mean(fitnesses)
            self.history["best"].append(es.result.fbest)
            self.history["mean"].append(mean_val)
            self.history["sigma"].append(es.sigma)

            generation += 1
            if verbose and generation % 5 == 0:
                print(
                    f"代 {generation}: "
                    f"最优={es.result.fbest:.6f}, "
                    f"平均={mean_val:.6f}, "
                    f"sigma={es.sigma:.4f}"
                )

            if callback:
                callback(np.array(es.result.xbest), es.result.fbest)

        self.result = es.result
        best_params = np.array(es.result.xbest)
        best_params = self.param_space.clip(best_params)

        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {es.result.fbest:.6f}")
            print(f"总评估次数: {es.result.evaluations}")
            print(f"最终 sigma: {es.sigma:.6f}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), best_params):
                print(f"  {name}: {value:.6f}")

        return best_params

    def get_convergence_data(self) -> Dict:
        """获取收敛数据"""
        return {
            "generations": np.arange(len(self.history["best"])),
            "best": np.array(self.history["best"]),
            "mean": np.array(self.history["mean"]),
            "sigma": np.array(self.history["sigma"]),
        }
