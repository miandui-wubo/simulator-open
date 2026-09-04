"""
LLM辅助的液滴实验参数搜索

利用LLM的物理知识来指导参数搜索：
1. 基于热毛细效应、Marangoni效应的物理知识
2. 检测不合理的参数组合
3. 建议搜索策略
"""

import numpy as np
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.droplet_parameters import (
    create_droplet_experiment_parameter_space,
    get_initial_guess_from_literature,
    print_parameter_summary,
    REFERENCE_DATA,
    PARAMETER_SENSITIVITY_PRIOR
)
from src.llm.llm_optimizer import LLMOptimizer
from examples.droplet_experiment import DropletSimulator, DropletObjective, EXPERIMENTAL_DATA, OBSERVABLE_WEIGHTS


# =============================================================================
# 液滴实验专用的LLM提示词
# =============================================================================

DROPLET_SYSTEM_PROMPT = """你是一位液态金属热物理学专家，专门研究液滴的热毛细迁移和润湿行为。

你精通以下领域：
- Marangoni效应（热毛细效应）：表面张力梯度驱动的流动
- 液滴润湿动力学：接触角、三相接触线行为
- 热传导：温度场分布、热扩散
- 液态金属特性：Ga, GaIn, GaInSn等液态金属的物理性质

你的任务是帮助优化液滴实验的仿真参数，使仿真结果与实验数据匹配。

关键物理知识：
1. Marangoni数 Ma = (dγ/dT)(ΔT)(L) / (μα) 决定热毛细效应强度
2. 液滴迁移速度 v ~ (dγ/dT)(dT/dx) / μ
3. 接触角滞后会影响液滴启动
4. 液态金属通常有高表面张力（0.5-0.7 N/m）和低粘度（~0.002 Pa·s）
5. 温度升高通常降低表面张力
"""


DROPLET_SUGGESTION_PROMPT = """
# 液滴实验参数优化

## 当前参数范围（13个参数）
{parameter_info}

## 优化历史
最近的评估结果：
{evaluation_history}

当前最优：
- 参数: {best_params}
- 误差: {best_error}

## 实验目标值
{experimental_targets}

## 请提供建议

基于你对液滴热毛细迁移的物理理解，请建议下一组参数：

考虑因素：
1. 如果液滴速度太慢，可能需要增大温度梯度或减小粘度
2. 如果速度太快，可能需要相反调整
3. 接触角会影响液滴的形状和启动条件
4. 表面张力是Marangoni效应的关键参数
5. 导热系数影响温度分布

请返回JSON格式：
{{
    "suggested_params": {{
        "left_substrate_temperature": float,
        "right_substrate_temperature": float,
        "left_contact_angle": float,
        "right_contact_angle": float,
        "surface_tension": float,
        "left_substrate_density": float,
        "right_substrate_density": float,
        "left_heat_capacity": float,
        "right_heat_capacity": float,
        "droplet_density": float,
        "droplet_viscosity": float,
        "left_thermal_conductivity": float,
        "right_thermal_conductivity": float
    }},
    "reasoning": "你的物理推理过程",
    "key_insight": "关键发现",
    "confidence": 0.0-1.0
}}
"""


DROPLET_CONSTRAINT_CHECK_PROMPT = """
# 液滴实验参数物理约束检查

请检查以下参数组合是否物理合理：

{params}

检查要点：
1. 温度范围是否合理（305-315K对液态金属是否太低？）
2. 表面张力值是否符合液态金属特性（通常0.5-0.7 N/m）
3. 粘度范围（0.1-0.3 Pa·s）是否适合液态金属（通常更低，~0.002 Pa·s）
4. 接触角是否在合理范围
5. 左右基板属性的差异是否能产生足够的驱动力
6. 热物性参数之间的一致性

返回JSON格式：
{{
    "is_reasonable": true/false,
    "physical_issues": ["问题列表"],
    "suggestions": ["改进建议"],
    "marangoni_estimate": "对Marangoni效应强度的估计",
    "expected_behavior": "预期的液滴行为"
}}
"""


class DropletLLMOptimizer(LLMOptimizer):
    """
    针对液滴实验优化的LLM优化器
    
    包含液滴物理学的专业知识
    """
    
    def __init__(
        self,
        param_space,
        objective,
        experimental_data: dict,
        model: str = "gpt-4",
        api_key: str = None
    ):
        super().__init__(param_space, objective, model, api_key)
        self.experimental_data = experimental_data
        
        # 使用液滴专用系统提示
        self.system_prompt = DROPLET_SYSTEM_PROMPT
    
    def suggest_next_params(self, n_suggestions: int = 1):
        """基于液滴物理知识建议参数"""
        
        # 格式化参数信息
        param_info = self._format_parameter_info()
        history_info = self._format_evaluation_history()
        exp_targets = json.dumps(self.experimental_data, indent=2)
        
        prompt = DROPLET_SUGGESTION_PROMPT.format(
            parameter_info=param_info,
            evaluation_history=history_info,
            best_params=self.best_params,
            best_error=self.best_value,
            experimental_targets=exp_targets
        )
        
        suggestions = []
        for _ in range(n_suggestions):
            response = self._call_llm(prompt, temperature=0.7)
            
            try:
                result = json.loads(response)
                params_dict = result.get("suggested_params", {})
                params_array = self.param_space.dict_to_array(params_dict)
                params_array = self.param_space.clip(params_array)
                suggestions.append(params_array)
                
                # 打印LLM的推理
                if 'reasoning' in result:
                    print(f"\n  LLM推理: {result['reasoning'][:100]}...")
                if 'key_insight' in result:
                    print(f"  关键发现: {result['key_insight']}")
                    
            except Exception as e:
                print(f"解析LLM响应失败: {e}")
                suggestions.append(self.param_space.sample(1)[0])
        
        return suggestions
    
    def check_physical_reasonableness(self, params):
        """使用液滴物理知识检查参数"""
        params_dict = self.param_space.array_to_dict(params)
        
        prompt = DROPLET_CONSTRAINT_CHECK_PROMPT.format(
            params=json.dumps(params_dict, indent=2)
        )
        
        response = self._call_llm(prompt, temperature=0.3)
        
        try:
            result = json.loads(response)
            
            # 打印检查结果
            if not result.get('is_reasonable', True):
                print(f"\n  ⚠️ 物理问题: {result.get('physical_issues', [])}")
            if result.get('expected_behavior'):
                print(f"  预期行为: {result['expected_behavior']}")
                
            return result
            
        except:
            return {"is_reasonable": True}
    
    def analyze_sensitivity(self) -> dict:
        """
        分析参数敏感性
        
        基于优化历史分析哪些参数对结果影响最大
        """
        if len(self.evaluation_history) < 10:
            return {"status": "insufficient_data", "message": "需要更多评估数据"}
        
        # 简单的敏感性分析
        params_array = np.array([h['params'] for h in self.evaluation_history])
        values = np.array([h['value'] for h in self.evaluation_history])
        
        correlations = {}
        for i, p in enumerate(self.param_space.parameters):
            corr = np.corrcoef(params_array[:, i], values)[0, 1]
            correlations[p.name] = corr
        
        # 按敏感性排序
        sorted_params = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        
        return {
            "status": "success",
            "correlations": correlations,
            "most_sensitive": [p[0] for p in sorted_params[:5]],
            "least_sensitive": [p[0] for p in sorted_params[-3:]]
        }


# =============================================================================
# 主程序
# =============================================================================

def main():
    """运行LLM辅助的液滴参数搜索"""
    
    print("=" * 70)
    print("LLM辅助液滴实验参数搜索")
    print("=" * 70)
    
    # 检查API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️ 未找到 OPENAI_API_KEY 环境变量")
        print("请设置: export OPENAI_API_KEY='your-api-key'")
        print("\n将使用随机策略代替LLM建议...")
    else:
        print("\n✓ 已找到API密钥，将使用GPT-4辅助搜索")
    
    # 创建参数空间
    param_space = create_droplet_experiment_parameter_space()
    print_parameter_summary(param_space)
    
    # 创建仿真器和目标函数
    simulator = DropletSimulator(simulation_type='mock')
    objective = DropletObjective(
        simulator=simulator,
        experimental_data=EXPERIMENTAL_DATA,
        weights=OBSERVABLE_WEIGHTS,
        param_space=param_space
    )
    
    # 创建LLM优化器
    llm_optimizer = DropletLLMOptimizer(
        param_space=param_space,
        objective=objective,
        experimental_data=EXPERIMENTAL_DATA,
        model="gpt-4",
        api_key=api_key
    )
    
    # 运行优化
    print(f"\n{'='*70}")
    print("开始LLM辅助搜索...")
    print(f"{'='*70}")
    
    best_params = llm_optimizer.optimize(
        n_iterations=30,
        n_random_init=5,
        check_reasonableness=True,
        verbose=True
    )
    
    # 敏感性分析
    print(f"\n{'='*70}")
    print("参数敏感性分析")
    print(f"{'='*70}")
    
    sensitivity = llm_optimizer.analyze_sensitivity()
    if sensitivity['status'] == 'success':
        print("\n最敏感参数 (影响最大):")
        for p in sensitivity['most_sensitive']:
            corr = sensitivity['correlations'][p]
            print(f"  - {p}: 相关系数 = {corr:.4f}")
        
        print("\n最不敏感参数 (影响最小):")
        for p in sensitivity['least_sensitive']:
            corr = sensitivity['correlations'][p]
            print(f"  - {p}: 相关系数 = {corr:.4f}")
    
    # 结果输出
    print(f"\n{'='*70}")
    print("最优参数")
    print(f"{'='*70}")
    
    best_params_dict = param_space.array_to_dict(best_params)
    for p in param_space.parameters:
        print(f"  {p.physical_meaning}: {best_params_dict[p.name]:.4f} {p.unit}")
    
    print(f"\n最终误差: {llm_optimizer.best_value:.6f}")
    print(f"总评估次数: {len(llm_optimizer.evaluation_history)}")
    
    print(f"\n{'='*70}")
    print("LLM辅助搜索完成!")
    print(f"{'='*70}")
    
    return best_params_dict


if __name__ == "__main__":
    main()

