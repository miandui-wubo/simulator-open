# 方法论：材料参数搜索的系统化方法

## 问题定义

### 核心挑战

在材料计算科学中，我们经常面临以下问题：

**给定：**
- 仿真软件（MD/DFT/FEM）
- 实验观测数据
- 参数的可能范围

**目标：**
找到一组参数 θ*，使得：

```
θ* = argmin_θ L(S(θ), E)
```

其中：
- S(θ): 使用参数θ的仿真结果
- E: 实验数据
- L: 损失函数（通常是某种误差度量）

**挑战：**
1. **计算成本高**：单次仿真可能需要几分钟到几天
2. **黑盒优化**：无法获得梯度信息
3. **高维空间**：通常有5-20个参数
4. **多峰景观**：可能存在多个局部最优
5. **噪声**：仿真和实验都有随机性

---

## 方法1：贝叶斯优化（Bayesian Optimization）

### 原理

贝叶斯优化通过构建目标函数的概率代理模型（通常是高斯过程），在探索和利用之间取得平衡。

**算法流程：**

1. 初始随机采样n₀个点
2. 用数据拟合高斯过程 GP(μ, σ²)
3. 计算采集函数 α(θ) = EI(θ) 或 UCB(θ)
4. 选择下一个评估点：θ_next = argmax α(θ)
5. 评估 f(θ_next)
6. 更新GP，重复2-5

**采集函数：**

- **Expected Improvement (EI)**:
  ```
  EI(θ) = E[max(f_best - f(θ), 0)]
  ```
  
- **Upper Confidence Bound (UCB)**:
  ```
  UCB(θ) = μ(θ) - κ·σ(θ)
  ```

### 优势与局限

✅ **优势：**
- 样本效率高（适合昂贵仿真）
- 自动平衡探索-利用
- 提供不确定性估计

❌ **局限：**
- 高维性能下降（>20维）
- GP拟合成本随样本数增长
- 可能陷入局部最优

### 适用场景

- MD仿真（每次评估>1分钟）
- DFT计算（每次评估>10分钟）
- 参数维度 < 15

### 实现细节

```python
# 关键参数选择
BayesianOptimizer(
    n_initial_points=max(10, 2*dim),  # 初始点数
    acquisition_func='EI',             # EI更保守，UCB更激进
    xi=0.01,                          # EI的exploration参数
    kappa=1.96                        # UCB的exploration参数
)
```

---

## 方法2：遗传算法（Genetic Algorithm）

### 原理

模拟生物进化过程：选择、交叉、变异。

**算法流程：**

1. 随机初始化种群 P₀
2. 评估每个个体的适应度
3. 选择（锦标赛/轮盘赌）
4. 交叉（SBX/单点交叉）
5. 变异（多项式变异/高斯变异）
6. 替换旧种群，重复2-5

**关键算子：**

- **Simulated Binary Crossover (SBX)**:
  ```
  child₁ = 0.5[(1-β)parent₁ + (1+β)parent₂]
  child₂ = 0.5[(1+β)parent₁ + (1-β)parent₂]
  ```

- **Polynomial Mutation**:
  ```
  x' = x + δ·(upper - lower)
  ```

### 优势与局限

✅ **优势：**
- 全局搜索能力强
- 不需要梯度
- 易于并行化
- 对初始值不敏感

❌ **局限：**
- 需要较多评估次数
- 参数调节敏感
- 收敛速度相对慢

### 适用场景

- 复杂非凸优化
- 可并行评估
- 需要全局最优
- 参数维度 5-50

### 实现细节

```python
GeneticAlgorithm(
    population_size=10*dim,      # 种群大小
    crossover_prob=0.7,          # 交叉概率
    mutation_prob=0.2,           # 变异概率
    tournament_size=3,           # 锦标赛大小
    eta_crossover=20.0,          # SBX参数
    eta_mutation=20.0            # 变异参数
)
```

**调参建议：**
- 种群太小：易陷入局部最优
- 种群太大：收敛慢
- 变异率太高：破坏好的解
- 变异率太低：缺乏多样性

---

## 方法3：粒子群优化（PSO）

### 原理

模拟鸟群/鱼群的群体智能。每个粒子根据自己的经验和群体经验更新位置。

**更新公式：**

```
v_i(t+1) = w·v_i(t) + c₁r₁(p_i - x_i) + c₂r₂(g - x_i)
x_i(t+1) = x_i(t) + v_i(t+1)
```

其中：
- w: 惯性权重
- c₁: 个体学习因子
- c₂: 社会学习因子
- p_i: 个体最优
- g: 全局最优

### 优势与局限

✅ **优势：**
- 实现简单
- 收敛快
- 参数少
- 易于并行

❌ **局限：**
- 易陷入局部最优
- 对参数敏感
- 缺乏全局探索机制

### 适用场景

- 中等维度问题（5-30维）
- 需要快速获得较好解
- 连续优化问题

### 实现细节

```python
ParticleSwarmOptimizer(
    n_particles=30,
    w=0.7,           # 惯性权重 [0.4-0.9]
    c1=1.5,          # 个体学习因子 [1.5-2.0]
    c2=1.5,          # 社会学习因子 [1.5-2.0]
    v_max_factor=0.2 # 最大速度限制
)
```

---

## 方法4：LLM辅助搜索（创新方法）

### 动机

传统优化方法不利用领域知识。LLM训练了大量物理/化学文献，可以：

1. 建议物理上合理的参数
2. 排除不合理的组合
3. 解释搜索策略
4. 诊断收敛问题

### 工作流程

```
1. [传统搜索] → 生成候选点
2. [LLM检查] → 物理合理性验证
3. [LLM建议] → 基于物理直觉的新候选点
4. [混合策略] → 结合传统+LLM建议
5. [诊断] → LLM分析收敛状况
```

### 提示词设计

**参数建议：**
```
基于以下优化历史和物理约束，建议下一个参数组合：
- 历史最优：{best_params}
- 物理约束：{constraints}
请返回JSON格式的参数建议和推理过程。
```

**合理性检查：**
```
检查参数组合的物理合理性：
{params}
考虑：热力学一致性、材料特性、相关性约束
返回是否合理及违反的约束。
```

### 优势与局限

✅ **优势：**
- 融合领域知识
- 减少无效评估
- 提供可解释性
- 自适应搜索策略

❌ **局限：**
- 需要API调用（成本）
- LLM可能产生幻觉
- 效果依赖提示词设计
- 不保证收敛

### 适用场景

- 参数有明确物理意义
- 存在已知约束关系
- 需要可解释的搜索过程
- 愿意承担API成本

---

## 方法5：多智能体协作搜索

### 架构

```
Coordinator
    ├── Explorer Agents (全局探索)
    │   ├── Agent 1: 随机跳跃 + 避免已访问区域
    │   ├── Agent 2: 不同探索策略
    │   └── ...
    │
    └── Exploiter Agents (局部优化)
        ├── Agent 1: 在Explorer发现的区域精细搜索
        ├── Agent 2: 梯度下降式搜索
        └── ...
```

### 通信机制

```python
# 周期性通信
if iteration % communication_interval == 0:
    # 1. 共享最优位置
    global_best = coordinator.get_global_best()
    
    # 2. Explorers学习其他发现
    for explorer in explorers:
        explorer.learn_from_others(all_bests)
    
    # 3. Exploiters跳转到有希望的区域
    for exploiter in exploiters:
        exploiter.accept_suggestion(good_position)
```

### 优势与局限

✅ **优势：**
- 平衡全局+局部搜索
- 天然并行
- 避免过早收敛
- 鲁棒性强

❌ **局限：**
- 实现复杂
- 需要调节通信频率
- 可能产生冗余评估

### 适用场景

- 复杂多峰问题
- 可以并行评估
- 需要全局+局部搜索
- 有充足计算资源

---

## 方法选择决策树

```
START
  │
  ├─ 单次评估 < 10秒?
  │   YES → PSO / 网格搜索
  │   NO ↓
  │
  ├─ 单次评估 > 10分钟?
  │   YES → 贝叶斯优化
  │   NO ↓
  │
  ├─ 维度 > 20?
  │   YES → 遗传算法 / 差分进化
  │   NO ↓
  │
  ├─ 有领域知识可用?
  │   YES → LLM辅助 + 贝叶斯优化
  │   NO ↓
  │
  ├─ 可以并行评估?
  │   YES → 多智能体 / 遗传算法
  │   NO → 贝叶斯优化
  │
  └─ 需要全局最优?
      YES → 多智能体 / 遗传算法
      NO → PSO / 贝叶斯优化
```

---

## 性能对比（理论分析）

| 方法 | 样本效率 | 全局搜索 | 收敛速度 | 并行性 | 可解释性 |
|------|---------|---------|---------|--------|---------|
| 贝叶斯优化 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 遗传算法 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 粒子群 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| LLM辅助 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 多智能体 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 实践建议

### 1. 初步探索阶段

```python
# 使用快速方法快速了解landscape
pso = ParticleSwarmOptimizer(...)
initial_best = pso.optimize(n_iterations=50)
```

### 2. 精细优化阶段

```python
# 在有希望的区域用贝叶斯优化
param_space_refined = refine_space_around(initial_best)
bo = BayesianOptimizer(param_space_refined, ...)
final_best = bo.optimize(n_iterations=100)
```

### 3. 验证阶段

```python
# 多次运行验证稳定性
results = []
for seed in range(10):
    result = run_optimization(seed=seed)
    results.append(result)

mean_best = np.mean([r.best_value for r in results])
std_best = np.std([r.best_value for r in results])
```

### 4. 组合策略

```python
# 混合多种方法
# 1. PSO粗搜索
# 2. GA全局精搜
# 3. BO局部精调
# 4. LLM验证合理性
```

---

## 理论保证

### 贝叶斯优化

**遗憾界**（Regret Bound）：
```
R_n = O(√(n·γ_n·log n))
```
其中 γ_n 是信息增益，对于GP通常是多项式级。

### 遗传算法

**Schema定理**：良好的building blocks会指数增长。

**收敛性**：在适当条件下，遗传算法几乎必然收敛到全局最优（但可能需要指数时间）。

### PSO

**收敛性**：在适当的参数设置下，PSO收敛到局部最优的充要条件：
```
w < 1, c₁ + c₂ < 4
```

---

## 参考文献

1. **Bayesian Optimization**
   - Mockus, J. (1989). Bayesian Approach to Global Optimization
   - Shahriari et al. (2016). Taking the Human Out of the Loop

2. **Genetic Algorithms**
   - Holland, J. (1975). Adaptation in Natural and Artificial Systems
   - Deb, K. (2001). Multi-Objective Optimization using Evolutionary Algorithms

3. **Particle Swarm Optimization**
   - Kennedy & Eberhart (1995). Particle Swarm Optimization
   - Shi & Eberhart (1998). Modified Particle Swarm Optimizer

4. **Multi-Agent Systems**
   - Dorigo & Stützle (2004). Ant Colony Optimization
   - Wooldridge (2009). An Introduction to MultiAgent Systems

5. **LLM for Science**
   - Boiko et al. (2023). Autonomous chemical research with LLMs
   - Jablonka et al. (2024). 14 examples of how LLMs can transform materials science

---

## 结论

参数搜索没有"最好"的方法，只有"最合适"的方法。关键是：

1. **了解问题特性**：评估成本、维度、景观复杂度
2. **匹配算法特点**：根据问题选择合适方法
3. **迭代改进**：从粗到精，从探索到利用
4. **验证稳定性**：多次运行确保结果可靠
5. **融合领域知识**：利用物理约束和先验信息


