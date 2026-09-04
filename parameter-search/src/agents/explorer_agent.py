"""探索智能体 - 负责全局搜索"""

import numpy as np
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.base_agent import BaseAgent


class ExplorerAgent(BaseAgent):
    """
    探索智能体
    
    职责：
    - 在参数空间中进行全局探索
    - 发现新的有希望的区域
    - 避免在已知区域重复搜索
    """
    
    def __init__(
        self,
        agent_id: str,
        param_space,
        objective,
        exploration_rate: float = 0.8,
        step_size: float = 0.3
    ):
        """
        初始化探索智能体
        
        Args:
            agent_id: 智能体ID
            param_space: 参数空间
            objective: 目标函数
            exploration_rate: 探索率（vs 随机）
            step_size: 步长（相对于参数范围）
        """
        super().__init__(agent_id, param_space, objective, role="explorer")
        self.exploration_rate = exploration_rate
        self.step_size = step_size
        self.visited_regions = []
    
    def step(self) -> Dict[str, Any]:
        """
        执行探索步骤
        
        策略：
        1. 以一定概率进行随机跳跃（探索新区域）
        2. 否则，从当前位置附近搜索
        3. 避免访问过的区域
        """
        if np.random.random() < self.exploration_rate:
            # 探索：随机跳跃到未访问区域
            self.current_position = self._explore_new_region()
        else:
            # 开发：在当前位置附近搜索
            self.current_position = self._local_search()
        
        # 评估新位置
        value = self.evaluate_current()
        
        # 记录访问区域
        self._record_visited_region(self.current_position)
        
        return {
            'agent_id': self.agent_id,
            'action': 'explore',
            'position': self.current_position.copy(),
            'value': value
        }
    
    def _explore_new_region(self) -> np.ndarray:
        """探索新区域"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            # 随机采样
            candidate = self.param_space.sample(1)[0]
            
            # 检查是否在已访问区域
            if not self._is_visited(candidate):
                return candidate
        
        # 如果尝试多次仍在已访问区域，返回随机位置
        return self.param_space.sample(1)[0]
    
    def _local_search(self) -> np.ndarray:
        """局部搜索"""
        if self.current_position is None:
            return self.param_space.sample(1)[0]
        
        # 在当前位置附近采样
        bounds = np.array(self.param_space.get_bounds())
        ranges = bounds[:, 1] - bounds[:, 0]
        
        # 添加高斯扰动
        perturbation = np.random.normal(0, self.step_size * ranges, size=len(self.param_space))
        new_position = self.current_position + perturbation
        
        # 确保在边界内
        new_position = self.param_space.clip(new_position)
        
        return new_position
    
    def _is_visited(self, position: np.ndarray, threshold: float = 0.1) -> bool:
        """检查位置是否已访问过"""
        if not self.visited_regions:
            return False
        
        # 计算与所有访问区域的距离
        for region_center in self.visited_regions:
            distance = np.linalg.norm(
                self.param_space.normalize(position) - 
                self.param_space.normalize(region_center)
            )
            if distance < threshold:
                return True
        
        return False
    
    def _record_visited_region(self, position: np.ndarray):
        """记录访问的区域"""
        # 只保留最近的一定数量的区域中心
        max_regions = 20
        
        self.visited_regions.append(position.copy())
        
        if len(self.visited_regions) > max_regions:
            self.visited_regions.pop(0)
    
    def learn_from_others(self, other_bests: list):
        """从其他智能体学习"""
        # 如果发现其他智能体有更好的结果，有一定概率跳到附近
        for other_pos, other_val in other_bests:
            if other_val < self.best_value:
                if np.random.random() < 0.3:  # 30%概率
                    # 跳到其他智能体的最优位置附近
                    self.current_position = self._local_search_around(other_pos)
                    break
    
    def _local_search_around(self, position: np.ndarray) -> np.ndarray:
        """在指定位置附近搜索"""
        bounds = np.array(self.param_space.get_bounds())
        ranges = bounds[:, 1] - bounds[:, 0]
        
        perturbation = np.random.normal(0, 0.1 * ranges, size=len(self.param_space))
        new_position = position + perturbation
        
        return self.param_space.clip(new_position)


