# 液滴接触角自主仿真与参数搜索系统

基于 **LLM 多智能体 + COMSOL/MATLAB/LAMMPS 联合仿真** 的液滴物理参数逆向搜索
完整技术栈：从对话式仿真助手，到多优化器参数搜索框架，到大规模批处理生产管线，
再到点云接触角后处理。

系统围绕一个核心问题：**液态金属（如 GaInSn）液滴在异质基板（如 Si/GaN）间的
接触角仿真，依赖大量缺失或不准确的物性参数**。本系统通过实验接触角数据反演，
自动搜索 13 个物理参数（表面张力、密度、粘度、基板热物性、温度、接触角等），
使仿真收敛到实验测量值（容差 ±1°）。

## 系统组成（四大组件）

### 1. `comsol_work/` — 对话式多智能体仿真助手

基于 LLM 意图识别的多 agent 协同体，三种工作模式：

- **chatting 模式**：材料领域知识问答（物性参数查询、LAMMPS/COMSOL 设置咨询）
- **lammps 模式**：为液滴分子动力学仿真提供关键物性参数（熔点、表面张力、
  密度、粘度、热导率）与模拟设置支持
- **experiment 模式**：根据用户描述的液滴/基板材料自主补全参数，调用
  COMSOL-MATLAB 完成液滴三维接触角仿真

运行：配置 `DEEPSEEK_API_KEY` 环境变量后运行 `main.py`。
（依赖 DeepSeek API；LLM 代码生成模板在 `model/matlab_infer.py`，可用本地模型替代）

### 2. `parameter-search/` — 参数搜索算法框架

实际用于仿真生产的三种参数搜索优化器，统一基于参数空间与目标函数抽象：

- **贝叶斯优化**（scikit-optimize，GP）：昂贵仿真评估的首选，样本效率高
- **遗传算法**（DEAP，SBX 交叉 + 多项式变异）：全局搜索，适合复杂非凸问题
- **粒子群优化 PSO**：快速收敛，适合中等维度

均支持早停收敛判定、GA 热启动种子、逐次评估历史记录。

### 3. `simulator/` — 批量参数搜索生产管线

把优化器框架应用于多实验批量搜索的工程化管线（COMSOL + MATLAB 真实仿真）：

- **三种优化器批处理脚本**：`run_batch_{bayesian,ga}*.sh`、`--optimizer pso`，
  支持按阶段顺序执行（`run_sequential_optimizer_batches.sh`）
- **断点续跑**：批处理按实验粒度持久化进度，中断重启自动跳过已完成实验
- **GA 热启动**：`SIMULATOR_WARM_START_EXPERIMENTS=exp_XXX` 使未收敛实验
  从历史 trace 接续进化（种子个体携带已知适应度，不重复消耗仿真评估）
- **并发安全**：文件锁串行化 COMSOL 评估、陈旧锁自动回收、
  环境变量隔离支持多实例
- **分析工具**：优化轨迹分析（`analyze_optimization_trace.py`）、
  单参数/多参数敏感性分析（`sensitivity_*.py`）
- **可选 LLM 代码生成**：本地小模型生成 MATLAB 参数段模板，
  不可用时自动回退确定性模板，不依赖外部 API

```bash
python -m simulator.main --experiments-csv input/experiments_preprocessed.csv \
    --optimizer ga --iterations 30 --tolerance 1.0     # 单命令批处理
bash simulator/run_batch_ga_full.sh                    # 或使用封装脚本
```

### 4. `contact-angle/` — 点云接触角计算

从 COMSOL 导出的三维点云计算接触角（Santiso 协方差矩阵/PCA 方法）：
接触线识别 → k 近邻局部切平面法向 → 与固体表面法向点积求接触角。
被主管线 `contact_angle_interface.py` 调用，也可独立使用。

## 环境依赖

- Python ≥ 3.10：`numpy scipy pandas scikit-optimize deap scikit-learn matplotlib openai`
- COMSOL Multiphysics 6.1（含 LiveLink for MATLAB）
- MATLAB（批处理模式 `matlab -batch`）
- 对话助手需 DeepSeek API key：`export DEEPSEEK_API_KEY=sk-...`

## 快速开始

```bash
# 1) 准备实验定义 CSV（experiment_id、目标接触角、材料、基板温度等列）
# 2) 运行批处理（结果输出到 simulation_workspace/）
bash simulator/run_batch_ga_full.sh
# 3) 分析单个实验的优化轨迹
python -m simulator.analyze_optimization_trace simulation_workspace/exp_001
# 4) 或直接对话式使用仿真助手
cd comsol_work && python main.py
```

## 说明

- 仓库只包含核心代码；实验测量数据、仿真结果、模型权重均不入库
- 各组件可独立使用，也可按"助手补全参数 → 管线批量搜索 → 接触角评估"串联
