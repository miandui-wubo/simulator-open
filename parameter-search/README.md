# 参数搜索算法框架

为液态金属合金液滴仿真提供的三种（实际用于仿真生产的）参数搜索优化器，
统一基于 `core/` 的参数空间与目标函数抽象：

| 优化器 | 实现 | 特点 |
|---|---|---|
| 贝叶斯优化 `bayesian_optimizer.py` | scikit-optimize (GP) | 高昂仿真评估的首选，样本效率高 |
| 遗传算法 `genetic_algorithm.py` | DEAP（SBX 交叉 + 多项式变异） | 全局搜索能力强，适合复杂非凸问题 |
| 粒子群优化 `pso_optimizer.py` | 自研实现 | 快速收敛，适合中等维度 |

三种优化器均支持：

- 早停收敛判定（`OptimizationConverged`，误差低于容差即终止）
- 热启动种子（GA：`seed_points` 携带已知适应度的初始种群）
- 逐次评估历史记录（`evaluation_history`，用于 trace 与收敛曲线）

`simulator/` 批处理管线通过 `--optimizer {bayesian,ga,pso}` 直接调用本框架。
