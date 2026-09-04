"""智能体基类"""

import numpy as np
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective


class BaseAgent(ABC):
    """
    智能体基类
    
    每个智能体负责在参数空间中搜索最优参数
    """
    
    def __init__(
        self,
        agent_id: str,
        param_space: ParameterSpace,
        objective: BaseObjective,
        role: str = "explorer"
    ):
        """
        初始化智能体
        
        Args:
            agent_id: 智能体ID
            param_space: 参数空间
            objective: 目标函数
            role: 角色类型 ('explorer', 'exploiter', 'coordinator')
        """
        self.agent_id = agent_id
        self.param_space = param_space
        self.objective = objective
        self.role = role
        
        # 智能体状态
        self.current_position = None
        self.best_position = None
        self.best_value = float('inf')
        self.history = []
        
        # 通信相关
        self.messages = []
        self.shared_knowledge = {}
    
    @abstractmethod
    def step(self) -> Dict[str, Any]:
        """
        执行一步搜索
        
        Returns:
            步骤结果字典
        """
        pass
    
    def initialize(self):
        """初始化智能体位置"""
        self.current_position = self.param_space.sample(1)[0]
        self.evaluate_current()
    
    def evaluate_current(self) -> float:
        """评估当前位置"""
        value = self.objective(self.current_position)
        
        # 更新历史
        self.history.append({
            'position': self.current_position.copy(),
            'value': value,
            'iteration': len(self.history)
        })
        
        # 更新最优
        if value < self.best_value:
            self.best_value = value
            self.best_position = self.current_position.copy()
        
        return value
    
    def receive_message(self, message: Dict[str, Any]):
        """接收来自其他智能体的消息"""
        self.messages.append(message)
    
    def send_message(self, recipient: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息给其他智能体"""
        return {
            'sender': self.agent_id,
            'recipient': recipient,
            'content': content
        }
    
    def share_best_position(self) -> Dict[str, Any]:
        """分享最佳位置"""
        return {
            'agent_id': self.agent_id,
            'position': self.best_position.copy() if self.best_position is not None else None,
            'value': self.best_value
        }
    
    def update_shared_knowledge(self, knowledge: Dict[str, Any]):
        """更新共享知识"""
        self.shared_knowledge.update(knowledge)
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'current_position': self.current_position,
            'best_value': self.best_value,
            'n_evaluations': len(self.history)
        }
    
    def __repr__(self) -> str:
        return f"Agent(id={self.agent_id}, role={self.role}, best={self.best_value:.6f})"


class CommunicationProtocol:
    """智能体间通信协议"""
    
    def __init__(self):
        self.message_queue = []
    
    def send(self, message: Dict[str, Any]):
        """发送消息"""
        self.message_queue.append(message)
    
    def broadcast(self, sender: str, content: Dict[str, Any]):
        """广播消息"""
        self.message_queue.append({
            'sender': sender,
            'recipient': 'all',
            'content': content
        })
    
    def deliver_messages(self, agents: List[BaseAgent]):
        """分发消息给智能体"""
        for message in self.message_queue:
            recipient = message['recipient']
            
            if recipient == 'all':
                # 广播给所有智能体
                for agent in agents:
                    if agent.agent_id != message['sender']:
                        agent.receive_message(message)
            else:
                # 发送给特定智能体
                for agent in agents:
                    if agent.agent_id == recipient:
                        agent.receive_message(message)
                        break
        
        # 清空消息队列
        self.message_queue = []


