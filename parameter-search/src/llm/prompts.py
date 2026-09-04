"""LLM提示词模板"""

SYSTEM_PROMPT = """你是一位材料科学和计算物理学专家，专门研究液态金属合金的热力学性质。
你精通以下领域：
- 第一性原理计算（Density Functional Theory, DFT）
- 分子动力学模拟（Molecular Dynamics, MD）
- 有限元方法（Finite Element Method, FEM）
- 热力学参数拟合和优化

你的任务是帮助优化仿真参数，使仿真结果与实验数据更好地匹配。"""


PARAMETER_SUGGESTION_PROMPT = """
# 任务描述
我们正在优化液态金属合金的仿真参数，使仿真结果与实验数据匹配。

# 参数空间
{parameter_info}

# 优化历史
已评估的参数组合：
{evaluation_history}

# 当前最优结果
最优参数：{best_params}
最优误差：{best_error}

# 物理约束和知识
{physical_constraints}

# 请提供建议
基于你的物理知识和优化历史，请建议下一个应该评估的参数组合。
考虑以下因素：
1. 物理合理性（参数之间的关系和约束）
2. 探索未搜索的区域
3. 在有希望的区域进行局部搜索
4. 避免不合理的参数组合

请以JSON格式返回，包含：
{{
    "suggested_params": {{"param_name": value, ...}},
    "reasoning": "你的推理过程",
    "confidence": 0.0-1.0,
    "exploration_score": 0.0-1.0
}}
"""


PHYSICAL_CONSTRAINT_CHECK_PROMPT = """
# 参数合理性检查

请检查以下参数组合是否物理上合理：

{params}

考虑以下物理约束：
1. Cauchy关系：对于某些金属，剪切模量和体积模量的关系
2. 热力学一致性：如Cp > Cv
3. 温度相关性：如扩散系数应随温度增加
4. 材料特性：基于材料类型的合理范围
5. 相关性：某些参数之间存在物理上的依赖关系

返回JSON格式：
{{
    "is_reasonable": true/false,
    "violations": ["违反的约束列表"],
    "suggestions": ["改进建议"],
    "severity": "low/medium/high"
}}
"""


PARAMETER_RANGE_REFINEMENT_PROMPT = """
# 参数范围细化

基于当前的搜索结果，我们需要细化参数搜索范围。

# 当前参数范围
{current_ranges}

# 优化结果分析
{optimization_analysis}

# 任务
请基于优化结果，建议是否需要调整搜索范围：
1. 如果最优值接近边界，建议扩大该参数范围
2. 如果某个参数在某个小范围内表现最好，建议缩小范围进行精细搜索
3. 基于物理知识，排除不合理的区域

返回JSON格式：
{{
    "refinements": {{
        "param_name": {{
            "new_lower": value,
            "new_upper": value,
            "reason": "原因"
        }},
        ...
    }},
    "overall_strategy": "下一步搜索策略建议"
}}
"""


ANOMALY_DETECTION_PROMPT = """
# 异常结果检测

在参数优化过程中，我们观察到以下结果：

{suspicious_results}

# 正常结果范围
{normal_results_stats}

# 任务
请判断这些结果是否异常，可能的原因：
1. 仿真收敛问题
2. 参数组合导致物理上不稳定的系统
3. 数值误差
4. 真实的物理现象

返回JSON格式：
{{
    "is_anomalous": true/false,
    "anomaly_type": "convergence_issue/physical_instability/numerical_error/normal",
    "recommendation": "应该丢弃/重新评估/接受",
    "explanation": "详细解释"
}}
"""


MULTI_OBJECTIVE_BALANCING_PROMPT = """
# 多目标优化权重调整

我们正在优化多个目标：

{objectives_info}

# 当前表现
{current_performance}

# 任务
基于材料应用场景和物理重要性，建议各目标的权重：

应用场景：{application_scenario}

返回JSON格式：
{{
    "suggested_weights": {{"objective_name": weight, ...}},
    "reasoning": "权重分配的理由",
    "trade_offs": "需要注意的权衡"
}}
"""


LITERATURE_KNOWLEDGE_PROMPT = """
# 文献知识查询

对于以下材料体系：

材料组成：{material_composition}
温度范围：{temperature_range}
压力条件：{pressure_condition}

# 任务
基于你的知识，提供文献中该材料体系的典型参数范围：

返回JSON格式：
{{
    "typical_values": {{
        "param_name": {{
            "value": typical_value,
            "range": [min, max],
            "references": "相关文献或数据库",
            "confidence": 0.0-1.0
        }},
        ...
    }},
    "notes": "额外说明"
}}
"""


CONVERGENCE_DIAGNOSIS_PROMPT = """
# 收敛诊断

优化过程的收敛曲线：

{convergence_data}

# 任务
诊断优化收敛状况，建议下一步行动：

1. 是否已经收敛？
2. 是否陷入局部最优？
3. 是否需要调整优化器参数？
4. 是否需要重启或采用不同策略？

返回JSON格式：
{{
    "convergence_status": "converged/slow_convergence/stuck/diverging",
    "is_local_optimum": true/false,
    "recommendations": [
        "具体建议列表"
    ],
    "next_action": "continue/restart/change_strategy/refine_range"
}}
"""


EXPERIMENT_DESIGN_PROMPT = """
# 实验设计

基于当前了解的参数空间结构：

{parameter_landscape_info}

# 任务
设计一组信息量最大的实验点（参数组合），用于：
1. 探索未知区域
2. 验证假设
3. 精细化搜索

使用准则：
- D-optimal: 最大化参数估计的精度
- 空间填充：均匀覆盖参数空间
- 自适应：基于已有信息的不确定性

返回JSON格式：
{{
    "experiment_points": [
        {{"params": {{...}}, "purpose": "exploration/exploitation/validation"}},
        ...
    ],
    "design_strategy": "设计策略说明",
    "expected_information_gain": "预期的信息增益"
}}
"""


