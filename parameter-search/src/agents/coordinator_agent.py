"""协调智能体 - 协调多个智能体的搜索"""

import numpy as np
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective
from src.agents.base_agent import BaseAgent, CommunicationProtocol
from src.agents.explorer_agent import ExplorerAgent
from src.agents.exploiter_agent import ExploiterAgent


class MultiAgentCoordinator:
    """
    多智能体协调器
    
    职责：
    - 管理多个智能体
    - 协调探索和利用
    - 信息共享和知识整合
    - 动态调整策略
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        n_explorers: int = 5,
        n_exploiters: int = 3,
        communication_interval: int = 5,
        diversity_weight: float = 0.3
    ):
        """
        初始化多智能体协调器
        
        Args:
            param_space: 参数空间
            objective: 目标函数
            n_explorers: 探索智能体数量
            n_exploiters: 利用智能体数量
            communication_interval: 通信间隔
            diversity_weight: 多样性权重
        """
        self.param_space = param_space
        self.objective = objective
        self.communication_interval = communication_interval
        self.diversity_weight = diversity_weight
        
        # 创建智能体
        self.explorers = [
            ExplorerAgent(
                agent_id=f"explorer_{i}",
                param_space=param_space,
                objective=objective
            )
            for i in range(n_explorers)
        ]
        
        self.exploiters = [
            ExploiterAgent(
                agent_id=f"exploiter_{i}",
                param_space=param_space,
                objective=objective
            )
            for i in range(n_exploiters)
        ]
        
        self.all_agents = self.explorers + self.exploiters
        
        # 通信协议
        self.comm_protocol = CommunicationProtocol()
        
        # 全局状态
        self.global_best_position = None
        self.global_best_value = float('inf')
        self.iteration = 0
        
        # 历史记录
        self.history = {
            'global_best': [],
            'diversity': [],
            'agent_performance': {agent.agent_id: [] for agent in self.all_agents}
        }
    
    def run(
        self,
        max_iterations: int = 200,
        convergence_threshold: float = 1e-6,
        patience: int = 20,
        verbose: bool = True
    ) -> np.ndarray:
        """
        运行多智能体搜索
        
        Args:
            max_iterations: 最大迭代次数
            convergence_threshold: 收敛阈值
            patience: 早停耐心值
            verbose: 是否打印进度
            
        Returns:
            最优参数
        """
        if verbose:
            print(f"启动多智能体搜索系统")
            print(f"探索智能体: {len(self.explorers)}, 利用智能体: {len(self.exploiters)}")
        
        # 初始化所有智能体
        for agent in self.all_agents:
            agent.initialize()
        
        # 更新全局最优
        self._update_global_best()
        
        no_improvement_count = 0
        
        # 主循环
        for iteration in range(max_iterations):
            self.iteration = iteration
            
            # 1. 所有智能体执行一步
            for agent in self.all_agents:
                result = agent.step()
            
            # 2. 更新全局最优
            previous_best = self.global_best_value
            self._update_global_best()
            
            # 3. 周期性通信和协调
            if (iteration + 1) % self.communication_interval == 0:
                self._coordinate_agents()
            
            # 4. 记录历史
            self._record_history()
            
            # 5. 检查收敛
            improvement = previous_best - self.global_best_value
            
            if improvement < convergence_threshold:
                no_improvement_count += 1
            else:
                no_improvement_count = 0
            
            # 6. 打印进度
            if verbose and (iteration + 1) % 10 == 0:
                diversity = self._calculate_diversity()
                print(f"迭代 {iteration+1}/{max_iterations}: "
                      f"全局最优={self.global_best_value:.6f}, "
                      f"多样性={diversity:.4f}")
            
            # 7. 早停
            if no_improvement_count >= patience:
                if verbose:
                    print(f"在{iteration+1}次迭代后收敛")
                break
        
        if verbose:
            print(f"\n搜索完成!")
            print(f"最优值: {self.global_best_value:.6f}")
            print(f"总评估次数: {self.objective.n_evaluations}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), 
                                   self.global_best_position):
                print(f"  {name}: {value:.6f}")
        
        return self.global_best_position
    
    def _update_global_best(self):
        """更新全局最优"""
        for agent in self.all_agents:
            if agent.best_value < self.global_best_value:
                self.global_best_value = agent.best_value
                self.global_best_position = agent.best_position.copy()
    
    def _coordinate_agents(self):
        """协调智能体"""
        # 1. 收集所有智能体的最优位置
        all_bests = [
            (agent.best_position, agent.best_value)
            for agent in self.all_agents
            if agent.best_position is not None
        ]
        
        # 2. 探索智能体学习其他智能体的发现
        for explorer in self.explorers:
            explorer.learn_from_others(all_bests)
        
        # 3. 利用智能体跳转到探索智能体发现的好位置
        # 找到探索智能体中表现最好的几个
        explorer_bests = sorted(
            [(e.best_position, e.best_value) for e in self.explorers],
            key=lambda x: x[1]
        )
        
        for i, exploiter in enumerate(self.exploiters):
            if i < len(explorer_bests):
                pos, val = explorer_bests[i]
                exploiter.accept_suggestion(pos, val)
        
        # 4. 广播全局最优
        self.comm_protocol.broadcast(
            sender='coordinator',
            content={
                'global_best_position': self.global_best_position,
                'global_best_value': self.global_best_value
            }
        )
        
        # 5. 分发消息
        self.comm_protocol.deliver_messages(self.all_agents)
    
    def _calculate_diversity(self) -> float:
        """计算智能体种群的多样性"""
        positions = [
            agent.current_position
            for agent in self.all_agents
            if agent.current_position is not None
        ]
        
        if len(positions) < 2:
            return 0.0
        
        # 计算所有对之间的平均距离
        positions = np.array(positions)
        normalized_positions = np.array([
            self.param_space.normalize(pos) for pos in positions
        ])
        
        total_distance = 0.0
        count = 0
        
        for i in range(len(normalized_positions)):
            for j in range(i + 1, len(normalized_positions)):
                distance = np.linalg.norm(
                    normalized_positions[i] - normalized_positions[j]
                )
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    def _record_history(self):
        """记录历史信息"""
        self.history['global_best'].append(self.global_best_value)
        self.history['diversity'].append(self._calculate_diversity())
        
        for agent in self.all_agents:
            self.history['agent_performance'][agent.agent_id].append(
                agent.best_value
            )
    
    def get_convergence_data(self) -> Dict[str, Any]:
        """获取收敛数据"""
        return {
            'iterations': np.arange(len(self.history['global_best'])),
            'global_best': np.array(self.history['global_best']),
            'diversity': np.array(self.history['diversity'])
        }
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        stats = {}
        
        for agent in self.all_agents:
            stats[agent.agent_id] = {
                'role': agent.role,
                'best_value': agent.best_value,
                'n_evaluations': len(agent.history),
                'performance_history': self.history['agent_performance'][agent.agent_id]
            }
        
        return stats
    
    def visualize_agents(self) -> Dict[str, Any]:
        """返回智能体位置用于可视化"""
        return {
            'explorers': [
                {
                    'id': e.agent_id,
                    'position': e.current_position,
                    'best_value': e.best_value
                }
                for e in self.explorers
                if e.current_position is not None
            ],
            'exploiters': [
                {
                    'id': e.agent_id,
                    'position': e.current_position,
                    'best_value': e.best_value
                }
                for e in self.exploiters
                if e.current_position is not None
            ],
            'global_best': {
                'position': self.global_best_position,
                'value': self.global_best_value
            }
        }


