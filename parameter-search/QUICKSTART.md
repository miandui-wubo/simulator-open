# 快速启动指南

## 5分钟入门

### 1. 安装

```bash
cd parameter-search
pip install -r requirements.txt
```

### 2. 运行第一个示例

```bash
python examples/simple_example.py
```

这将运行一个完整的参数搜索示例，对比三种不同的优化算法。

### 3. 查看结果

程序会生成 `optimizer_comparison.png`，展示不同算法的收敛性能。

---

## 你的第一个参数搜索

创建一个新文件 `my_search.py`：

```python
import numpy as np
from src.core.parameter_space import ParameterSpace
from src.core.objective import create_objective_from_function
from src.optimizers.bayesian_optimizer import BayesianOptimizer

# 1. 定义你的参数空间
param_space = ParameterSpace({
    'temperature': (300, 1500),    # K
    'pressure': (0.1, 10.0),       # GPa
    'composition': (0.0, 1.0)      # 摩尔分数
})

# 2. 定义你的目标函数（仿真）
def my_simulation(params):
    """
    params: numpy数组，顺序与参数空间定义一致
    返回: 误差值（越小越好）
    """
    # 这里替换为你的实际仿真代码
    # 例如：调用LAMMPS、VASP等
    
    # 示例：简单的测试函数
    temp, press, comp = params
    
    # 假设实验值
    exp_density = 2.7  # g/cm³
    
    # 模拟计算密度（这里用简单公式代替真实仿真）
    sim_density = 3.0 - 0.001*temp + 0.1*press - 0.5*comp
    
    # 计算误差
    error = abs(sim_density - exp_density)
    
    return error

# 3. 创建优化器
objective = create_objective_from_function(my_simulation)

optimizer = BayesianOptimizer(
    param_space=param_space,
    objective=objective
)

# 4. 运行优化
best_params = optimizer.optimize(n_iterations=30, verbose=True)

# 5. 查看结果
print("\n最优参数:")
param_dict = param_space.array_to_dict(best_params)
for name, value in param_dict.items():
    print(f"  {name}: {value:.4f}")

print(f"\n最优误差: {objective.best_value:.6f}")
```

运行：
```bash
python my_search.py
```

---

## 常见应用场景

### 场景A: MD力场参数拟合

如果你有LAMMPS并想拟合力场参数：

```python
# 1. 准备LAMMPS输入模板 (input.template)
# 2. 定义参数空间
param_space = ParameterSpace({
    'epsilon': (0.1, 0.5),  # eV
    'sigma': (2.5, 3.5),    # Å
    # ... 其他参数
})

# 3. 准备实验数据
experimental_data = {
    'density': np.array([2.7]),
    'msd': np.array([...]),
}

# 4. 连接LAMMPS
from src.core.simulator_interface import LAMMPSSimulator
simulator = LAMMPSSimulator(
    lammps_executable='lmp',
    template_file='input.template'
)

# 5. 定义目标函数
from src.core.objective import SimulationObjective
objective = SimulationObjective(
    simulator=simulator.run,
    experimental_data=experimental_data,
    observables=['density', 'msd']
)

# 6. 优化
optimizer = BayesianOptimizer(param_space, objective)
best_params = optimizer.optimize(n_iterations=50)
```

### 场景B: 使用LLM辅助（需要API密钥）

```python
# 设置API密钥
import os
os.environ['OPENAI_API_KEY'] = 'your-key-here'

# 使用LLM辅助优化器
from src.llm.llm_optimizer import LLMOptimizer

llm_optimizer = LLMOptimizer(
    param_space=param_space,
    objective=objective,
    model='gpt-4'
)

best_params = llm_optimizer.optimize(
    n_iterations=30,
    check_reasonableness=True  # LLM会检查物理合理性
)
```

### 场景C: 多智能体并行搜索

```python
from src.agents.coordinator_agent import MultiAgentCoordinator

coordinator = MultiAgentCoordinator(
    param_space=param_space,
    objective=objective,
    n_explorers=5,
    n_exploiters=3
)

best_params = coordinator.run(max_iterations=100)
```

---

## 选择合适的优化器

| 如果你的情况是... | 推荐使用 | 原因 |
|------------------|----------|------|
| 每次仿真 > 5分钟 | 贝叶斯优化 | 样本效率最高 |
| 参数空间很复杂 | 遗传算法 | 全局搜索能力强 |
| 想快速看到结果 | 粒子群优化 | 收敛速度快 |
| 有API密钥 | LLM辅助 | 利用物理知识 |
| 可以并行计算 | 多智能体 | 充分利用资源 |

---

## 调试技巧

### 问题：优化器一直报错

**检查：**
1. 参数空间定义是否正确
2. 目标函数是否总能返回数值
3. 仿真是否能正常运行

**建议：**
```python
# 先用MockObjective测试
from src.core.objective import MockObjective
test_obj = MockObjective(dimension=len(param_space))

# 确保优化器正常工作
optimizer = BayesianOptimizer(param_space, test_obj)
optimizer.optimize(n_iterations=10)

# 如果测试通过，再换成真实目标函数
```

### 问题：收敛太慢或陷入局部最优

**尝试：**
1. 增加初始随机采样点数
2. 切换到遗传算法
3. 使用多智能体方法
4. 缩小参数范围（如果有先验知识）

### 问题：仿真经常失败

**建议：**
```python
def robust_simulation(params):
    try:
        result = run_simulation(params)
        return compute_error(result)
    except Exception as e:
        print(f"仿真失败: {e}")
        return 1e6  # 返回大惩罚值
```

---

## 下一步

- 📖 阅读 [USAGE_GUIDE.md](USAGE_GUIDE.md) 了解详细用法
- 🔬 阅读 [METHODOLOGY.md](METHODOLOGY.md) 了解方法原理
- 💻 查看 `examples/` 目录获取更多示例
- 🎨 使用 `src/utils/visualization.py` 可视化结果

---

## 获取帮助

- 查看示例代码：`examples/`
- 阅读文档：`USAGE_GUIDE.md`
- 提交Issue：GitHub Issues

祝你参数搜索顺利！🚀


