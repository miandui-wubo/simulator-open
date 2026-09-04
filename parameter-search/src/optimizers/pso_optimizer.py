"""粒子群优化 - 快速收敛的群智能算法"""

import numpy as np
from typing import Optional, Callable
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective


class ParticleSwarmOptimizer:
    """
    粒子群优化（PSO）
    
    基于鸟群/鱼群行为的群智能优化算法。
    
    优点：
    - 实现简单
    - 收敛速度快
    - 参数少，易于调节
    - 可并行评估
    
    适用场景：
    - 中等维度的优化问题（5-50维）
    - 需要快速获得较好解
    - 连续优化问题
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        n_particles: int = 30,
        w: float = 0.7,  # 惯性权重
        c1: float = 1.5,  # 个体学习因子
        c2: float = 1.5,  # 社会学习因子
        v_max_factor: float = 0.2,  # 最大速度因子
        random_state: Optional[int] = None
    ):
        """
        初始化PSO
        
        Args:
            param_space: 参数空间
            objective: 目标函数
            n_particles: 粒子数量
            w: 惯性权重（通常0.4-0.9）
            c1: 个体学习因子（通常1.5-2.0）
            c2: 社会学习因子（通常1.5-2.0）
            v_max_factor: 最大速度系数（相对于搜索空间）
            random_state: 随机种子
        """
        self.param_space = param_space
        self.objective = objective
        self.n_particles = n_particles
        self.w = w
        self.c1 = c1
        self.c2 = c2
        
        if random_state is not None:
            np.random.seed(random_state)
        
        self.dim = len(param_space)
        bounds = np.array(param_space.get_bounds())
        self.lower_bounds = bounds[:, 0]
        self.upper_bounds = bounds[:, 1]
        
        # 计算最大速度
        search_range = self.upper_bounds - self.lower_bounds
        self.v_max = v_max_factor * search_range
        
        # 初始化粒子
        self.positions = None
        self.velocities = None
        self.personal_best_positions = None
        self.personal_best_values = None
        self.global_best_position = None
        self.global_best_value = float('inf')
        
        self.history = {
            'global_best': [],
            'mean_fitness': []
        }
    
    def _initialize_swarm(self):
        """初始化粒子群（串行评估，避免同时启动多个MATLAB）"""
        # 随机初始化位置
        self.positions = self.param_space.sample(self.n_particles)

        # 随机初始化速度
        self.velocities = np.random.uniform(
            -self.v_max,
            self.v_max,
            (self.n_particles, self.dim)
        )

        # 初始化个体最优（串行评估，逐个调用仿真）
        self.personal_best_positions = self.positions.copy()
        self.personal_best_values = np.zeros(self.n_particles)
        for i, pos in enumerate(self.positions):
            print(f"  [初始化] 评估粒子 {i+1}/{self.n_particles}...")
            self.personal_best_values[i] = self.objective(pos)

        # 初始化全局最优
        best_idx = np.argmin(self.personal_best_values)
        self.global_best_position = self.personal_best_positions[best_idx].copy()
        self.global_best_value = self.personal_best_values[best_idx]
    
    def _update_velocity(self):
        """更新粒子速度"""
        # 随机因子
        r1 = np.random.random((self.n_particles, self.dim))
        r2 = np.random.random((self.n_particles, self.dim))
        
        # 惯性项
        inertia = self.w * self.velocities
        
        # 个体学习项
        cognitive = self.c1 * r1 * (self.personal_best_positions - self.positions)
        
        # 社会学习项
        social = self.c2 * r2 * (self.global_best_position - self.positions)
        
        # 更新速度
        self.velocities = inertia + cognitive + social
        
        # 限制速度
        self.velocities = np.clip(self.velocities, -self.v_max, self.v_max)
    
    def _update_position(self):
        """更新粒子位置"""
        self.positions = self.positions + self.velocities
        
        # 边界处理：反弹
        for i in range(self.dim):
            # 下界反弹
            mask = self.positions[:, i] < self.lower_bounds[i]
            self.positions[mask, i] = self.lower_bounds[i]
            self.velocities[mask, i] *= -0.5
            
            # 上界反弹
            mask = self.positions[:, i] > self.upper_bounds[i]
            self.positions[mask, i] = self.upper_bounds[i]
            self.velocities[mask, i] *= -0.5
    
    def _update_best(self):
        """更新个体最优和全局最优（串行评估，避免同时启动多个MATLAB）"""
        # 评估当前位置（串行评估，逐个调用仿真）
        current_values = np.zeros(self.n_particles)
        for i, pos in enumerate(self.positions):
            current_values[i] = self.objective(pos)
        
        # 更新个体最优
        improved = current_values < self.personal_best_values
        self.personal_best_positions[improved] = self.positions[improved]
        self.personal_best_values[improved] = current_values[improved]
        
        # 更新全局最优
        best_idx = np.argmin(self.personal_best_values)
        if self.personal_best_values[best_idx] < self.global_best_value:
            self.global_best_position = self.personal_best_positions[best_idx].copy()
            self.global_best_value = self.personal_best_values[best_idx]
    
    def optimize(
        self,
        n_iterations: int = 100,
        verbose: bool = True,
        callback: Optional[Callable] = None
    ) -> np.ndarray:
        """
        执行PSO优化
        
        Args:
            n_iterations: 迭代次数
            verbose: 是否打印进度
            callback: 每次迭代后的回调函数
            
        Returns:
            最优参数
        """
        # 初始化
        self._initialize_swarm()
        
        if verbose:
            print(f"开始粒子群优化 (粒子数={self.n_particles}, 迭代={n_iterations})")
            print(f"初始最优值: {self.global_best_value:.6f}")
        
        # 迭代优化
        for iteration in range(n_iterations):
            # 更新速度和位置
            self._update_velocity()
            self._update_position()
            
            # 评估并更新最优
            self._update_best()
            
            # 记录历史
            self.history['global_best'].append(self.global_best_value)
            self.history['mean_fitness'].append(np.mean(self.personal_best_values))
            
            if verbose and (iteration + 1) % 10 == 0:
                print(f"迭代 {iteration+1}/{n_iterations}: "
                      f"全局最优={self.global_best_value:.6f}, "
                      f"平均适应度={np.mean(self.personal_best_values):.6f}")
            
            if callback:
                callback(self.global_best_position, self.global_best_value)
        
        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {self.global_best_value:.6f}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), 
                                   self.global_best_position):
                print(f"  {name}: {value:.6f}")
        
        return self.global_best_position
    
    def get_convergence_data(self):
        """获取收敛数据"""
        return {
            'iterations': np.arange(len(self.history['global_best'])),
            'global_best': np.array(self.history['global_best']),
            'mean_fitness': np.array(self.history['mean_fitness'])
        }
    
    def get_swarm_state(self):
        """获取当前粒子群状态（用于可视化）"""
        return {
            'positions': self.positions.copy(),
            'velocities': self.velocities.copy(),
            'personal_best': self.personal_best_positions.copy(),
            'global_best': self.global_best_position.copy()
        }


