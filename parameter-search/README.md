# 多智能体液态金属合金热力学参数自主搜索系统

## 项目简介

本项目旨在通过多智能体协作和先进的参数搜索算法，自动调整液态金属合金仿真参数，使仿真结果与实验数据匹配。

## 核心问题

在材料科学仿真中（FT/MD/FEM），公开参数可能：
- **缺失**：某些参数没有文献数据
- **不准确**：实验条件差异导致参数偏差

本系统通过智能参数搜索，找到使仿真与实验一致的最优参数组合。

## 方法论

### 1. 传统优化方法
- **贝叶斯优化**：适合昂贵的仿真评估（推荐）
- **遗传算法**：全局搜索，适合复杂非凸问题
- **粒子群优化**：快速收敛，适合中等维度
- **网格/随机搜索**：baseline方法

### 2. LLM辅助方法（创新）
- **知识引导搜索**：LLM基于物理知识建议参数范围
- **实验设计优化**：智能选择下一个评估点
- **异常检测**：识别不合理的参数组合
- **多模态推理**：结合文献、实验数据和仿真结果

### 3. 多智能体协作
- **探索智能体**：并行搜索不同参数区域
- **利用智能体**：局部精细化搜索
- **评估智能体**：运行仿真并评分
- **协调智能体**：整合信息，指导搜索策略

## 项目结构

```
parameter-search/
├── src/
│   ├── core/
│   │   ├── parameter_space.py      # 参数空间定义
│   │   ├── objective.py             # 目标函数（仿真vs实验）
│   │   └── simulator_interface.py  # 仿真器接口
│   ├── optimizers/
│   │   ├── bayesian_optimizer.py   # 贝叶斯优化
│   │   ├── genetic_algorithm.py    # 遗传算法
│   │   ├── pso_optimizer.py        # 粒子群优化
│   │   └── grid_search.py          # 网格搜索
│   ├── llm/
│   │   ├── llm_optimizer.py        # LLM辅助优化
│   │   ├── knowledge_base.py       # 物理知识库
│   │   └── prompts.py              # 提示词模板
│   ├── agents/
│   │   ├── base_agent.py           # 智能体基类
│   │   ├── explorer_agent.py       # 探索智能体
│   │   ├── exploiter_agent.py      # 利用智能体
│   │   └── coordinator_agent.py    # 协调智能体
│   └── utils/
│       ├── visualization.py        # 可视化工具
│       └── logger.py               # 日志记录
├── examples/
│   ├── simple_example.py           # 简单示例
│   ├── md_simulation.py            # 分子动力学示例
│   └── multi_agent_search.py      # 多智能体示例
├── tests/
├── requirements.txt
└── README.md
```

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 基础使用

```python
from src.core.parameter_space import ParameterSpace
from src.optimizers.bayesian_optimizer import BayesianOptimizer
from src.core.objective import ObjectiveFunction

# 1. 定义参数空间
param_space = ParameterSpace({
    'cohesive_energy': (3.0, 5.0),      # eV
    'lattice_constant': (3.5, 4.5),     # Å
    'bulk_modulus': (80, 150),          # GPa
    # ... 其他7个参数
})

# 2. 定义目标函数
def evaluate(params):
    sim_result = run_simulation(params)  # 运行仿真
    exp_data = load_experiment_data()    # 加载实验数据
    return compute_error(sim_result, exp_data)

objective = ObjectiveFunction(evaluate)

# 3. 选择优化器
optimizer = BayesianOptimizer(param_space, objective)

# 4. 运行搜索
best_params = optimizer.optimize(n_iterations=100)
```

### 使用LLM辅助搜索

```python
from src.llm.llm_optimizer import LLMOptimizer

# 使用GPT-4辅助搜索
optimizer = LLMOptimizer(
    param_space=param_space,
    objective=objective,
    model="gpt-4",
    use_knowledge_base=True
)

best_params = optimizer.optimize(n_iterations=50)
```

### 多智能体协作搜索

```python
from src.agents.coordinator_agent import MultiAgentCoordinator

coordinator = MultiAgentCoordinator(
    n_explorers=5,
    n_exploiters=3,
    param_space=param_space,
    objective=objective
)

best_params = coordinator.run(max_iterations=200)
```

## 主要特性

✅ **多种优化算法**：传统到前沿的参数搜索方法  
✅ **LLM集成**：利用大语言模型的物理知识  
✅ **多智能体**：并行探索，高效搜索  
✅ **可扩展**：轻松集成自定义仿真器  
✅ **可视化**：实时监控搜索进度  
✅ **容错性**：自动保存中间结果  

## 适用场景

- 分子动力学（MD）参数拟合
- 第一性原理（DFT/FT）计算参数校准
- 有限元（FEM）材料参数反演
- 热力学模型参数优化

## License

MIT License


