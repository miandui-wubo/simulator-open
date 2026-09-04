"""LLM辅助的参数优化器"""

import numpy as np
import json
from typing import Optional, Dict, List, Any, Callable
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective
from src.llm.prompts import *


class LLMOptimizer:
    """
    LLM辅助的参数优化器
    
    利用大语言模型的物理知识和推理能力来指导参数搜索。
    
    主要功能：
    1. 基于物理知识建议参数
    2. 检测不合理的参数组合
    3. 自适应调整搜索范围
    4. 诊断优化收敛问题
    
    优势：
    - 融合领域知识
    - 减少不合理评估
    - 提供可解释的搜索策略
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        use_knowledge_base: bool = True,
        hybrid_optimizer: Optional[Any] = None,
        llm_guidance_weight: float = 0.3
    ):
        """
        初始化LLM优化器
        
        Args:
            param_space: 参数空间
            objective: 目标函数
            model: LLM模型名称
            api_key: API密钥
            use_knowledge_base: 是否使用物理知识库
            hybrid_optimizer: 传统优化器（混合模式）
            llm_guidance_weight: LLM指导的权重（0-1）
        """
        self.param_space = param_space
        self.objective = objective
        self.model = model
        self.use_knowledge_base = use_knowledge_base
        self.hybrid_optimizer = hybrid_optimizer
        self.llm_guidance_weight = llm_guidance_weight
        
        # 初始化LLM客户端
        self.client = self._init_llm_client(api_key)
        
        # 评估历史
        self.evaluation_history = []
        self.best_params = None
        self.best_value = float('inf')
        
        # 物理约束知识库
        self.physical_constraints = self._load_physical_constraints()
    
    def _init_llm_client(self, api_key: Optional[str]):
        """初始化LLM客户端"""
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key is None:
            print("警告：未提供API密钥，LLM功能将受限")
            return None
        
        try:
            if "gpt" in self.model.lower():
                from openai import OpenAI
                return OpenAI(api_key=api_key)
            elif "claude" in self.model.lower():
                from anthropic import Anthropic
                return Anthropic(api_key=api_key)
            else:
                print(f"警告：未知模型 {self.model}")
                return None
        except Exception as e:
            print(f"LLM客户端初始化失败: {e}")
            return None
    
    def _load_physical_constraints(self) -> Dict[str, Any]:
        """加载物理约束知识"""
        # 这里可以从文件或数据库加载
        # 简化版本：硬编码一些基本约束
        return {
            "thermodynamic": {
                "cohesive_energy": "凝聚能应为正值，典型金属3-5 eV",
                "melting_point": "熔点应在材料类型的合理范围内",
            },
            "mechanical": {
                "bulk_modulus": "体积模量 > 剪切模量（通常）",
                "elastic": "杨氏模量与体积模量、剪切模量的关系",
            },
            "transport": {
                "diffusion": "扩散系数随温度呈Arrhenius关系",
                "viscosity": "粘度与温度反相关",
            }
        }
    
    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """调用LLM"""
        if self.client is None:
            return self._fallback_response()
        
        try:
            if "gpt" in self.model.lower():
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                return response.choices[0].message.content
            elif "claude" in self.model.lower():
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    system=SYSTEM_PROMPT,
                    temperature=temperature
                )
                return response.content[0].text
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """当LLM不可用时的后备响应"""
        sample = np.atleast_1d(self.param_space.sample(1)[0])
        return json.dumps({
            "suggested_params": self.param_space.array_to_dict(sample),
            "reasoning": "Random sampling (LLM unavailable)",
            "confidence": 0.5,
            "exploration_score": 1.0
        })
    
    def suggest_next_params(self, n_suggestions: int = 1) -> List[np.ndarray]:
        """
        基于LLM建议下一个参数组合
        
        Args:
            n_suggestions: 建议数量
            
        Returns:
            参数数组列表
        """
        # 准备提示词
        param_info = self._format_parameter_info()
        history_info = self._format_evaluation_history()
        
        prompt = PARAMETER_SUGGESTION_PROMPT.format(
            parameter_info=param_info,
            evaluation_history=history_info,
            best_params=self.best_params,
            best_error=self.best_value,
            physical_constraints=json.dumps(self.physical_constraints, indent=2)
        )
        
        suggestions = []
        for _ in range(n_suggestions):
            response = self._call_llm(prompt, temperature=0.7)
            
            try:
                result = json.loads(response)
                params_dict = result.get("suggested_params", {})
                params_array = self.param_space.dict_to_array(params_dict)
                
                # 确保在边界内
                params_array = self.param_space.clip(params_array)
                suggestions.append(params_array)
                
            except Exception as e:
                print(f"解析LLM响应失败: {e}")
                # 后备方案：随机采样
                suggestions.append(self.param_space.sample(1)[0])
        
        return suggestions
    
    def check_physical_reasonableness(self, params: np.ndarray) -> Dict[str, Any]:
        """
        检查参数的物理合理性
        
        Args:
            params: 参数数组
            
        Returns:
            检查结果字典
        """
        params_dict = self.param_space.array_to_dict(params)
        
        prompt = PHYSICAL_CONSTRAINT_CHECK_PROMPT.format(
            params=json.dumps(params_dict, indent=2)
        )
        
        response = self._call_llm(prompt, temperature=0.3)
        
        try:
            return json.loads(response)
        except:
            # 默认认为合理
            return {
                "is_reasonable": True,
                "violations": [],
                "suggestions": [],
                "severity": "low"
            }
    
    def optimize(
        self,
        n_iterations: int = 50,
        n_random_init: int = 5,
        check_reasonableness: bool = True,
        verbose: bool = True
    ) -> np.ndarray:
        """
        执行LLM辅助优化
        
        Args:
            n_iterations: 迭代次数
            n_random_init: 初始随机采样次数
            check_reasonableness: 是否检查物理合理性
            verbose: 是否打印详情
            
        Returns:
            最优参数
        """
        if verbose:
            print(f"开始LLM辅助优化 (模型: {self.model})")
        
        # 阶段1：随机初始化
        if verbose:
            print(f"\n阶段1: 随机探索 ({n_random_init}次)")
        
        for i in range(n_random_init):
            params = self.param_space.sample(1)[0]
            value = self.objective(params)
            
            self._update_history(params, value)
            
            if verbose:
                print(f"  初始化 {i+1}/{n_random_init}: f = {value:.6f}")
        
        # 阶段2：LLM指导搜索
        if verbose:
            print(f"\n阶段2: LLM指导搜索 ({n_iterations - n_random_init}次)")
        
        for i in range(n_random_init, n_iterations):
            # LLM建议参数
            suggestions = self.suggest_next_params(n_suggestions=3)
            
            # 如果启用合理性检查，过滤不合理的参数
            if check_reasonableness and self.client is not None:
                valid_suggestions = []
                for params in suggestions:
                    check_result = self.check_physical_reasonableness(params)
                    if check_result.get("is_reasonable", True):
                        valid_suggestions.append(params)
                    elif verbose:
                        print(f"  跳过不合理参数: {check_result.get('violations')}")
                
                suggestions = valid_suggestions if valid_suggestions else suggestions
            
            # 评估最佳建议
            if suggestions:
                params = suggestions[0]
                value = self.objective(params)
                
                self._update_history(params, value)
                
                if verbose:
                    improvement = ""
                    if value < self.best_value:
                        improvement = " ✓ NEW BEST"
                    print(f"  迭代 {i+1}/{n_iterations}: f = {value:.6f}{improvement}")
        
        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {self.best_value:.6f}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), self.best_params):
                print(f"  {name}: {value:.6f}")
        
        return self.best_params
    
    def _update_history(self, params: np.ndarray, value: float):
        """更新历史记录"""
        self.evaluation_history.append({
            'params': params.copy(),
            'value': value
        })
        
        if value < self.best_value:
            self.best_value = value
            self.best_params = params.copy()
    
    def _format_parameter_info(self) -> str:
        """格式化参数信息"""
        info = []
        for p in self.param_space.parameters:
            info.append(f"- {p.name}: [{p.lower_bound}, {p.upper_bound}] {p.unit or ''}")
            if p.physical_meaning:
                info.append(f"  含义: {p.physical_meaning}")
        return "\n".join(info)
    
    def _format_evaluation_history(self, max_recent: int = 10) -> str:
        """格式化评估历史（最近几次）"""
        if not self.evaluation_history:
            return "无历史记录"
        
        recent = self.evaluation_history[-max_recent:]
        lines = []
        for i, record in enumerate(recent, 1):
            params = np.atleast_1d(record['params'])
            params_dict = self.param_space.array_to_dict(params)
            lines.append(f"{i}. 误差={record['value']:.6f}")
            lines.append(f"   参数: {json.dumps(params_dict, indent=6)}")
        
        return "\n".join(lines)
    
    def diagnose_convergence(self) -> Dict[str, Any]:
        """诊断收敛状况"""
        if len(self.evaluation_history) < 10:
            return {"status": "insufficient_data"}
        
        values = [r['value'] for r in self.evaluation_history]
        
        prompt = CONVERGENCE_DIAGNOSIS_PROMPT.format(
            convergence_data=json.dumps({
                'values': values[-50:],  # 最近50次
                'best_value': self.best_value,
                'improvement_rate': (values[-10] - values[-1]) / 10
            })
        )
        
        response = self._call_llm(prompt, temperature=0.3)
        
        try:
            return json.loads(response)
        except:
            return {"status": "parse_error", "response": response}




