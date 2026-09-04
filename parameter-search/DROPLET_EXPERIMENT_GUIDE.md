# 液滴实验参数搜索使用指南

## 目标

**找到使仿真结果与实验结果一致的参数组合**

```
输入: 13个物理参数
    ↓
仿真: 液滴运动模拟 (COMSOL/OpenFOAM/自定义)
    ↓
输出: 液滴速度、位置、迁移时间等
    ↓
对比: 与实验观测值比较
    ↓
优化: 调整参数使误差最小
```

---

## 参数列表 (13个)

| 序号 | 参数名称 | 英文名 | 范围 | 单位 |
|------|---------|--------|------|------|
| 1 | 左基板温度 | left_substrate_temperature | (305, 315) | K |
| 2 | 右基板温度 | right_substrate_temperature | (305, 315) | K |
| 3 | 左基板接触角 | left_contact_angle | (15, 30) | deg |
| 4 | 右基板接触角 | right_contact_angle | (15, 30) | deg |
| 5 | 表面张力 | surface_tension | (0.1, 0.5) | N/m |
| 6 | 左基板密度 | left_substrate_density | (3000, 7000) | kg/m³ |
| 7 | 右基板密度 | right_substrate_density | (300, 700) | kg/m³ |
| 8 | 左基板恒压热容 | left_heat_capacity | (300, 700) | J/(kg·K) |
| 9 | 右基板恒压热容 | right_heat_capacity | (300, 1000) | J/(kg·K) |
| 10 | 液滴密度 | droplet_density | (3000, 7000) | kg/m³ |
| 11 | 液滴动力黏度 | droplet_viscosity | (0.1, 0.3) | Pa·s |
| 12 | 左基板导热系数 | left_thermal_conductivity | (100, 250) | W/(m·K) |
| 13 | 右基板导热系数 | right_thermal_conductivity | (30, 80) | W/(m·K) |

---

## 文献参考值

### 液滴材料 (Ga, GaIn, GaInSn)

| 属性 | Ga | GaIn | GaInSn | 来源 |
|-----|-----|------|--------|------|
| 密度 (kg/m³) | 5907 | 6250 | 6440 | Wikipedia, Sigma-Aldrich |
| 动力粘度 (Pa·s) | 1.87×10⁻³ | 2~4×10⁻³ | 2.4×10⁻³ | IOP Science, 知乎 |
| 表面张力 (N/m) | 0.5 | 0.624 | 0.718 | 文献 |

### 基板材料 (Si, GaN, GaAs)

| 属性 | Si | GaN | GaAs | 来源 |
|-----|-----|-----|------|------|
| 密度 (kg/m³) | 2329 | ~5800 | 5316 | Wikipedia |
| 导热系数 (W/(m·K)) | 150 | 130 | ~55 | 文献 |
| 热容 (J/(kg·K)) | 710 | 600* | 330* | *估计值 |

**注意**: 文献值仅供参考，实际值可能因实验条件而异。

---

## 快速开始

### 1. 安装依赖

```bash
cd parameter-search
pip install -r requirements.txt
```

### 2. 运行测试示例

```bash
# 使用Mock仿真器测试优化流程
python examples/droplet_experiment.py
```

### 3. 连接真实仿真器

修改 `examples/droplet_experiment.py` 中的 `DropletSimulator` 类：

```python
class DropletSimulator:
    def __init__(self, simulation_type: str = 'comsol'):
        self.simulation_type = simulation_type
    
    def run(self, params: dict) -> dict:
        if self.simulation_type == 'comsol':
            return self._run_comsol(params)
        elif self.simulation_type == 'openfoam':
            return self._run_openfoam(params)
        # ...
```

### 4. 填入实验数据

```python
EXPERIMENTAL_DATA = {
    'droplet_velocity': 0.05,        # 您的实验测量值
    'migration_distance': 0.002,     # 您的实验测量值
    'final_position': 0.008,         # 您的实验测量值
    'migration_time': 5.0,           # 您的实验测量值
    # ... 其他观测量
}
```

---

## 仿真器接口

### COMSOL (通过 mph 库)

```python
def _run_comsol(self, params: dict) -> dict:
    import mph
    
    # 启动COMSOL
    client = mph.start()
    model = client.load('droplet_model.mph')
    
    # 设置参数
    model.parameter('T_left', f'{params["left_substrate_temperature"]}[K]')
    model.parameter('T_right', f'{params["right_substrate_temperature"]}[K]')
    model.parameter('theta_left', f'{params["left_contact_angle"]}[deg]')
    model.parameter('theta_right', f'{params["right_contact_angle"]}[deg]')
    model.parameter('gamma', f'{params["surface_tension"]}[N/m]')
    model.parameter('rho_left', f'{params["left_substrate_density"]}[kg/m^3]')
    model.parameter('rho_right', f'{params["right_substrate_density"]}[kg/m^3]')
    model.parameter('cp_left', f'{params["left_heat_capacity"]}[J/(kg*K)]')
    model.parameter('cp_right', f'{params["right_heat_capacity"]}[J/(kg*K)]')
    model.parameter('rho_droplet', f'{params["droplet_density"]}[kg/m^3]')
    model.parameter('mu', f'{params["droplet_viscosity"]}[Pa*s]')
    model.parameter('k_left', f'{params["left_thermal_conductivity"]}[W/(m*K)]')
    model.parameter('k_right', f'{params["right_thermal_conductivity"]}[W/(m*K)]')
    
    # 求解
    model.solve()
    
    # 提取结果
    # 需要根据您的COMSOL模型定义调整
    velocity = model.evaluate('velocity_integral')
    position = model.evaluate('droplet_position')
    # ...
    
    return {
        'droplet_velocity': velocity,
        'final_position': position,
        # ...
    }
```

### OpenFOAM

```python
def _run_openfoam(self, params: dict) -> dict:
    import subprocess
    import os
    
    # 1. 修改OpenFOAM案例文件
    case_dir = 'droplet_case'
    
    # 修改 constant/transportProperties
    self._update_transport_properties(case_dir, params)
    
    # 修改 0/T (温度边界条件)
    self._update_temperature_bc(case_dir, params)
    
    # 2. 运行仿真
    subprocess.run(['blockMesh'], cwd=case_dir)
    subprocess.run(['interFoam'], cwd=case_dir)
    
    # 3. 后处理
    result = subprocess.run(
        ['postProcess', '-func', 'patchAverage'],
        cwd=case_dir,
        capture_output=True
    )
    
    # 4. 解析结果
    return self._parse_openfoam_results(case_dir)
```

### 自定义Python仿真

```python
def _run_custom_simulation(self, params: dict) -> dict:
    """
    如果有自己的Python数值模拟代码
    """
    from your_simulation_module import DropletSolver
    
    solver = DropletSolver()
    solver.set_parameters(params)
    solver.solve()
    
    return {
        'droplet_velocity': solver.get_velocity(),
        'final_position': solver.get_position(),
        # ...
    }
```

---

## 优化方法选择

### 方法1：贝叶斯优化 (推荐)

**适用场景**：每次仿真 > 1分钟

```python
from src.optimizers.bayesian_optimizer import BayesianOptimizer

optimizer = BayesianOptimizer(
    param_space=param_space,
    objective=objective,
    n_initial_points=15,  # 13参数，初始点稍多
    acquisition_func='EI'
)

best_params = optimizer.optimize(n_iterations=50)
```

**优点**：
- 样本效率高（30-50次评估即可收敛）
- 自动平衡探索和利用

### 方法2：多智能体搜索

**适用场景**：可以并行运行多个仿真

```python
from src.agents.coordinator_agent import MultiAgentCoordinator

coordinator = MultiAgentCoordinator(
    param_space=param_space,
    objective=objective,
    n_explorers=5,   # 全局探索
    n_exploiters=3   # 局部优化
)

best_params = coordinator.run(max_iterations=150)
```

**优点**：
- 全局搜索能力强
- 不易陷入局部最优

### 方法3：LLM辅助 (创新)

**适用场景**：希望利用物理知识

```python
# 需要设置 OPENAI_API_KEY
export OPENAI_API_KEY='your-key'

python examples/droplet_llm_search.py
```

**优点**：
- 利用Marangoni效应等物理知识
- 检测不合理的参数组合
- 提供可解释的搜索过程

---

## 常见问题

### Q1: 参数范围是否合理？

**粘度范围疑问**：
您设定的粘度范围 (0.1-0.3 Pa·s) 远大于液态金属的典型值 (~0.002 Pa·s)。

**可能原因**：
- 考虑了不同温度下的变化
- 考虑了液滴与基板的表观粘度
- 特定实验条件

**建议**：如果是液态金属，考虑调整范围到 (0.001, 0.01) Pa·s

### Q2: 仿真失败怎么办？

```python
def evaluate(self, params):
    try:
        result = simulator.run(params)
        return compute_error(result)
    except Exception as e:
        print(f"仿真失败: {e}")
        return 1e6  # 返回大惩罚值
```

### Q3: 如何加速搜索？

1. **使用代理模型**：先用简化模型筛选，再用精确模型验证
2. **并行评估**：多智能体方法支持并行
3. **缩小范围**：基于物理知识排除不合理区域
4. **使用LLM**：减少无效评估

### Q4: 如何判断是否收敛？

```python
# 观察收敛曲线
from src.utils.visualization import plot_convergence

data = optimizer.get_convergence_plot_data()
plot_convergence(data)

# 如果误差 < 0.01 (1%)，通常可以认为收敛
```

---

## 代码结构

```
examples/
├── droplet_experiment.py     # 主示例 ⭐
├── droplet_llm_search.py     # LLM辅助搜索

src/
├── core/
│   └── droplet_parameters.py # 13参数定义 ⭐
├── optimizers/
│   ├── bayesian_optimizer.py # 贝叶斯优化
│   └── ...
├── agents/
│   └── coordinator_agent.py  # 多智能体
└── llm/
    └── llm_optimizer.py      # LLM辅助
```

---

## 完整流程

```
1. 定义实验数据
   └── EXPERIMENTAL_DATA = {...}

2. 创建参数空间
   └── param_space = create_droplet_experiment_parameter_space()

3. 实现仿真器接口
   └── class DropletSimulator: def run(self, params) -> results

4. 创建目标函数
   └── objective = DropletObjective(simulator, experimental_data)

5. 选择优化器
   └── optimizer = BayesianOptimizer(...) 或 MultiAgentCoordinator(...)

6. 运行优化
   └── best_params = optimizer.optimize(n_iterations=50)

7. 验证结果
   └── simulator.run(best_params) 对比 experimental_data

8. 物理约束检查
   └── check_physical_constraints(best_params)
```

---

## 预期结果

使用贝叶斯优化，通常：
- **30-50次仿真**可以找到较好的参数
- **误差 < 5%** 是合理的目标
- **误差 < 1%** 需要更多迭代或更精确的仿真

---

## 下一步

1. **填入真实实验数据**：替换 `EXPERIMENTAL_DATA`
2. **实现仿真接口**：连接COMSOL/OpenFOAM
3. **运行优化**：`python examples/droplet_experiment.py`
4. **验证和调整**：根据结果调整参数范围

祝您的液滴实验参数搜索顺利！🚀

