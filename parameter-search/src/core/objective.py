"""目标函数模块 - 评估仿真与实验结果的差异"""

import numpy as np
from typing import Callable, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import time


class OptimizationConverged(Exception):
    """Raised after recording an evaluation that meets the stop criterion."""


class BaseObjective(ABC):
    """目标函数基类"""
    
    def __init__(self):
        self.n_evaluations = 0
        self.evaluation_history = []
        self.best_value = float('inf')
        self.best_params = None
    
    @abstractmethod
    def evaluate(self, params: np.ndarray) -> float:
        """
        评估参数，返回误差值（越小越好）
        
        Args:
            params: 参数数组
            
        Returns:
            误差值
        """
        pass
    
    def __call__(self, params: np.ndarray) -> float:
        """使对象可调用"""
        start_time = time.time()
        value = self.evaluate(params)
        eval_time = time.time() - start_time
        
        # 记录评估历史
        self.n_evaluations += 1
        self.evaluation_history.append({
            'params': params.copy(),
            'value': value,
            'time': eval_time,
            'iteration': self.n_evaluations
        })
        
        # 更新最佳值
        if value < self.best_value:
            self.best_value = value
            self.best_params = params.copy()

        if getattr(self, "stop_requested", False):
            reason = getattr(self, "stop_reason", "Optimization convergence criterion met.")
            raise OptimizationConverged(reason)
        
        return value
    
    def get_best(self) -> Tuple[np.ndarray, float]:
        """获取最佳参数和对应的值"""
        return self.best_params, self.best_value


class SimulationObjective(BaseObjective):
    """基于仿真的目标函数"""
    
    def __init__(
        self,
        simulator: Callable,
        experimental_data: Dict[str, np.ndarray],
        observables: List[str],
        weights: Optional[Dict[str, float]] = None
    ):
        """
        初始化仿真目标函数
        
        Args:
            simulator: 仿真函数，接受参数字典，返回观测量字典
            experimental_data: 实验数据 {'observable_name': array}
            observables: 需要匹配的观测量列表
            weights: 各观测量的权重
        """
        super().__init__()
        self.simulator = simulator
        self.experimental_data = experimental_data
        self.observables = observables
        
        # 默认权重为1
        self.weights = weights if weights else {obs: 1.0 for obs in observables}
        
        # 归一化权重
        total_weight = sum(self.weights.values())
        self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def evaluate(self, params: np.ndarray) -> float:
        """
        评估参数
        
        计算仿真结果与实验数据的加权均方根误差
        """
        try:
            # 运行仿真
            sim_results = self.simulator(params)
            
            # 计算每个观测量的误差
            total_error = 0.0
            
            for obs in self.observables:
                if obs not in sim_results or obs not in self.experimental_data:
                    continue
                
                sim_data = np.array(sim_results[obs])
                exp_data = self.experimental_data[obs]
                
                # 归一化均方根误差 (NRMSE)
                rmse = np.sqrt(np.mean((sim_data - exp_data) ** 2))
                nrmse = rmse / (np.max(exp_data) - np.min(exp_data) + 1e-10)
                
                total_error += self.weights[obs] * nrmse
            
            return total_error
        
        except Exception as e:
            # 如果仿真失败，返回一个很大的惩罚值
            print(f"Simulation failed: {e}")
            return 1e6


class MultiObjective(BaseObjective):
    """多目标优化函数"""
    
    def __init__(
        self,
        objectives: List[BaseObjective],
        weights: Optional[List[float]] = None,
        aggregation: str = 'weighted_sum'
    ):
        """
        初始化多目标函数
        
        Args:
            objectives: 目标函数列表
            weights: 权重列表
            aggregation: 聚合方法 ('weighted_sum', 'max', 'pareto')
        """
        super().__init__()
        self.objectives = objectives
        self.aggregation = aggregation
        
        if weights is None:
            weights = [1.0] * len(objectives)
        
        # 归一化权重
        total = sum(weights)
        self.weights = [w / total for w in weights]
    
    def evaluate(self, params: np.ndarray) -> float:
        """评估多个目标"""
        values = [obj(params) for obj in self.objectives]
        
        if self.aggregation == 'weighted_sum':
            return sum(w * v for w, v in zip(self.weights, values))
        elif self.aggregation == 'max':
            return max(values)
        else:
            raise ValueError(f"Unknown aggregation method: {self.aggregation}")
    
    def get_pareto_front(self) -> List[Dict]:
        """获取Pareto前沿（仅在记录了完整历史时有效）"""
        # 简化实现，实际应该实现非支配排序
        return sorted(self.evaluation_history, key=lambda x: x['value'])[:10]


class MockObjective(BaseObjective):
    """模拟目标函数（用于测试和演示）"""
    
    def __init__(self, dimension: int, noise_level: float = 0.01):
        """
        创建一个带噪声的测试函数
        
        Args:
            dimension: 参数维度
            noise_level: 噪声水平
        """
        super().__init__()
        self.dimension = dimension
        self.noise_level = noise_level
        
        # 生成一个随机的"真实"参数
        self.true_params = np.random.uniform(0.3, 0.7, dimension)
    
    def evaluate(self, params: np.ndarray) -> float:
        """
        计算参数与"真实"参数的距离
        模拟仿真与实验的差异
        """
        # 主要误差：欧式距离
        distance = np.linalg.norm(params - self.true_params)
        
        # 添加一些非线性交互项（模拟复杂的物理关系）
        interaction = 0.1 * np.sum(np.sin(10 * params) * np.cos(10 * self.true_params))
        
        # 添加高斯噪声（模拟实验和仿真的随机误差）
        noise = np.random.normal(0, self.noise_level)
        
        return distance + interaction + noise


# 便捷函数
def create_objective_from_function(func: Callable) -> BaseObjective:
    """从函数创建目标对象"""
    
    class FunctionObjective(BaseObjective):
        def __init__(self, f):
            super().__init__()
            self.f = f
        
        def evaluate(self, params):
            return self.f(params)
    
    return FunctionObjective(func)


