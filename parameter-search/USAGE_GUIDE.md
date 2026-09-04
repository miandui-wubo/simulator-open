# 使用指南

## 快速开始

### 1. 安装依赖

```bash
cd parameter-search
pip install -r requirements.txt
```

### 2. 运行示例

#### 简单示例：对比不同优化算法

```bash
python examples/simple_example.py
```

这将运行并对比以下三种优化算法：
- 贝叶斯优化（推荐用于昂贵仿真）
- 遗传算法（全局搜索）
- 粒子群优化（快速收敛）

#### 多智能体协作搜索

```bash
python examples/multi_agent_search.py
```

演示多个智能体（探索者+利用者）协作搜索参数空间。

#### LLM辅助搜索（需要API密钥）

```bash
export OPENAI_API_KEY='your-api-key-here'
python examples/llm_assisted_search.py
```

展示如何使用LLM的物理知识指导参数搜索。

#### MD参数拟合示例

```bash
python examples/md_simulation.py
```

模拟分子动力学力场参数拟合场景。

---

## 详细使用说明

### 场景1：简单参数优化

如果您有一个黑盒目标函数，想要找到最优参数：

```python
from src.core.parameter_space import ParameterSpace
from src.optimizers.bayesian_optimizer import BayesianOptimizer

# 定义参数空间
param_space = ParameterSpace({
    'param1': (0.0, 10.0),
    'param2': (1.0, 5.0),
    'param3': (0.1, 1.0)
})

# 定义目标函数
def my_objective(params):
    # params是一个numpy数组
    # 返回要最小化的值
    return some_expensive_simulation(params)

# 创建优化器
from src.core.objective import create_objective_from_function
objective = create_objective_from_function(my_objective)

optimizer = BayesianOptimizer(param_space, objective)

# 运行优化
best_params = optimizer.optimize(n_iterations=50)
```

**选择优化器的建议：**

| 优化器 | 适用场景 | 优点 | 缺点 |
|--------|----------|------|------|
| 贝叶斯优化 | 评估昂贵（分钟级） | 样本效率高 | 高维性能下降 |
| 遗传算法 | 复杂非凸问题 | 全局搜索能力强 | 需要更多评估 |
| 粒子群优化 | 中等维度 | 实现简单，收敛快 | 易陷入局部最优 |
| LLM辅助 | 有领域知识可用 | 利用物理直觉 | 需要API调用 |
| 多智能体 | 需要全局+局部搜索 | 并行探索 | 实现复杂 |

---

### 场景2：仿真参数拟合（与实验数据对比）

```python
from src.core.objective import SimulationObjective
from src.core.simulator_interface import MockSimulator

# 1. 准备仿真器
def run_simulation(params):
    # params是numpy数组，需要转换为仿真器接受的格式
    # 运行您的仿真（LAMMPS, VASP, COMSOL等）
    # 返回观测量字典
    return {
        'density': np.array([...]),
        'diffusion_coeff': np.array([...]),
        'viscosity': np.array([...])
    }

# 2. 准备实验数据
experimental_data = {
    'density': np.array([2.7]),  # g/cm³
    'diffusion_coeff': np.array([1.5e-9]),  # m²/s
    'viscosity': np.array([0.002])  # Pa·s
}

# 3. 创建目标函数
objective = SimulationObjective(
    simulator=run_simulation,
    experimental_data=experimental_data,
    observables=['density', 'diffusion_coeff', 'viscosity'],
    weights={'density': 0.4, 'diffusion_coeff': 0.4, 'viscosity': 0.2}
)

# 4. 优化
optimizer = BayesianOptimizer(param_space, objective)
best_params = optimizer.optimize(n_iterations=100)
```

---

### 场景3：使用LLM辅助（创新方法）

LLM可以利用物理知识来：
1. 建议合理的参数值
2. 检测不合理的参数组合
3. 提供搜索策略建议

```python
from src.llm.llm_optimizer import LLMOptimizer

llm_optimizer = LLMOptimizer(
    param_space=param_space,
    objective=objective,
    model="gpt-4",  # 或 "claude-3-opus"
    use_knowledge_base=True
)

# 运行优化
best_params = llm_optimizer.optimize(
    n_iterations=50,
    check_reasonableness=True  # 启用物理合理性检查
)

# 诊断收敛
diagnosis = llm_optimizer.diagnose_convergence()
print(diagnosis)
```

**优势：**
- 减少不合理评估（节省计算资源）
- 融合文献知识
- 提供可解释的搜索过程

---

### 场景4：多智能体协作搜索

适合需要全局探索+局部优化的复杂问题：

```python
from src.agents.coordinator_agent import MultiAgentCoordinator

coordinator = MultiAgentCoordinator(
    param_space=param_space,
    objective=objective,
    n_explorers=5,    # 探索智能体数量
    n_exploiters=3,   # 利用智能体数量
    communication_interval=5
)

best_params = coordinator.run(
    max_iterations=200,
    verbose=True
)

# 查看智能体性能
stats = coordinator.get_agent_statistics()
```

**适用场景：**
- 参数空间复杂，有多个局部最优
- 可以并行评估多个参数组合
- 需要平衡探索和利用

---

## 高级功能

### 1. 自定义参数空间

```python
from src.core.parameter_space import Parameter, ParameterSpace

params = [
    Parameter(
        name='cohesive_energy',
        lower_bound=3.0,
        upper_bound=5.0,
        scale='linear',  # 或 'log'
        unit='eV',
        description='Cohesive energy',
        physical_meaning='原子间结合能'
    ),
    # ... 更多参数
]

param_space = ParameterSpace(params)
```

### 2. 可视化

```python
from src.utils.visualization import (
    plot_convergence,
    plot_parameter_evolution,
    plot_2d_parameter_space
)

# 收敛曲线
plot_convergence(
    optimizer.get_convergence_plot_data(),
    save_path='convergence.png'
)

# 参数演化
plot_parameter_evolution(
    objective.evaluation_history,
    param_space.get_param_names(),
    save_path='param_evolution.png'
)

# 2D空间轨迹
plot_2d_parameter_space(
    objective.evaluation_history,
    param_indices=(0, 1),
    param_names=param_space.get_param_names(),
    save_path='search_trajectory.png'
)
```

### 3. 保存和加载结果

```python
import pickle

# 保存优化器状态
with open('optimizer_state.pkl', 'wb') as f:
    pickle.dump({
        'best_params': optimizer.best_params,
        'best_value': optimizer.best_value,
        'history': objective.evaluation_history
    }, f)

# 加载
with open('optimizer_state.pkl', 'rb') as f:
    state = pickle.load(f)
```

---

## 连接真实仿真软件

### LAMMPS（分子动力学）

```python
from src.core.simulator_interface import LAMMPSSimulator

simulator = LAMMPSSimulator(
    lammps_executable="/path/to/lmp",
    template_file="input.template"
)

simulator.setup()
results = simulator.run(params_dict)
simulator.cleanup()
```

**input.template示例：**

```lammps
# LAMMPS输入文件模板
units metal
atom_style atomic

pair_style lj/cut ${cutoff}
pair_coeff * * ${epsilon} ${sigma}

# ... 其他LAMMPS命令
```

### VASP/Quantum ESPRESSO（第一性原理）

类似地，可以创建自定义仿真器：

```python
from src.core.simulator_interface import BaseSimulator

class VASPSimulator(BaseSimulator):
    def run(self, params):
        # 生成INCAR, POSCAR等
        # 运行VASP
        # 解析OUTCAR
        return observables
```

---

## 性能优化技巧

### 1. 并行评估

```python
from concurrent.futures import ProcessPoolExecutor

def parallel_evaluate(param_list):
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = executor.map(objective, param_list)
    return list(results)
```

### 2. 使用代理模型加速

对于极其昂贵的仿真，可以训练神经网络代理：

```python
# 先用少量真实仿真训练代理模型
# 然后用代理模型进行初步筛选
# 最后用真实仿真验证最优候选
```

### 3. 自适应采样

```python
# 在不确定性高的区域增加采样密度
# 贝叶斯优化天然支持这一点
```

---

## 故障排除

### 问题1：优化陷入局部最优

**解决方案：**
- 使用遗传算法或多智能体方法
- 增加初始随机采样点
- 调整采集函数参数（贝叶斯优化）

### 问题2：收敛太慢

**解决方案：**
- 减小参数空间范围（利用先验知识）
- 使用更激进的利用策略
- 考虑使用粒子群优化

### 问题3：仿真经常失败

**解决方案：**
- 在目标函数中添加try-except处理
- 返回大惩罚值而非抛出异常
- 使用LLM检查参数合理性

### 问题4：维度太高（>20维）

**解决方案：**
- 使用差分进化或遗传算法
- 考虑降维或参数分组
- 使用TPE而非高斯过程

---

## 引用和参考

如果这个项目对您的研究有帮助，请引用：

```bibtex
@software{parameter_search_2024,
  title = {Multi-Agent Parameter Search for Materials Simulation},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourname/parameter-search}
}
```

**相关文献：**

1. Bayesian Optimization: Shahriari et al., "Taking the Human Out of the Loop: A Review of Bayesian Optimization", IEEE, 2016
2. Genetic Algorithms: Forrest, "Genetic algorithms: principles of natural selection applied to computation", Science, 1993
3. Multi-Agent Systems: Dorigo & Birattari, "Swarm intelligence", Scholarpedia, 2007
4. LLM for Scientific Discovery: Boiko et al., "Autonomous chemical research with large language models", Nature, 2023

---

## 联系和支持

- Issues: [GitHub Issues](https://github.com/yourname/parameter-search/issues)
- Documentation: [Read the Docs](https://parameter-search.readthedocs.io)
- Email: your.email@example.com

---

## License

MIT License - 详见LICENSE文件


