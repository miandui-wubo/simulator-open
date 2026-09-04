"""遗传算法 - 适合全局搜索和复杂非凸问题"""

import numpy as np
from typing import Optional, Callable, List, Tuple
from deap import base, creator, tools, algorithms
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective


class GeneticAlgorithm:
    """
    遗传算法优化器
    
    基于自然选择和遗传学原理的全局优化算法。
    
    优点：
    - 全局搜索能力强
    - 不需要梯度信息
    - 能处理非凸、多峰问题
    - 可并行评估
    
    适用场景：
    - 复杂的非凸优化landscape
    - 需要全局最优解
    - 可以并行评估多个参数组合
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        population_size: int = 50,
        crossover_prob: float = 0.7,
        mutation_prob: float = 0.2,
        tournament_size: int = 3,
        eta_crossover: float = 20.0,
        eta_mutation: float = 20.0,
        random_state: Optional[int] = None,
        seed_points: Optional[List[Tuple[np.ndarray, float]]] = None
    ):
        """
        初始化遗传算法

        Args:
            param_space: 参数空间
            objective: 目标函数
            population_size: 种群大小
            crossover_prob: 交叉概率
            mutation_prob: 变异概率
            tournament_size: 锦标赛选择的大小
            eta_crossover: SBX交叉的分布指数
            eta_mutation: 多项式变异的分布指数
            random_state: 随机种子
            seed_points: 热启动种子 [(参数数组, 已知误差)]，替换初始种群并携带
                已知适应度，使进化从上一轮进度继续而不重跑 COMSOL
        """
        self.param_space = param_space
        self.objective = objective
        self.population_size = population_size
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.tournament_size = tournament_size
        self.eta_crossover = eta_crossover
        self.eta_mutation = eta_mutation
        self.seed_points = list(seed_points) if seed_points else None
        
        if random_state is not None:
            np.random.seed(random_state)
        
        self._setup_deap()
        
        self.history = {
            'best': [],
            'mean': [],
            'std': []
        }
    
    def _setup_deap(self):
        """设置DEAP框架"""
        # 清除可能存在的类型
        if hasattr(creator, "FitnessMin"):
            del creator.FitnessMin
        if hasattr(creator, "Individual"):
            del creator.Individual
        
        # 创建fitness和individual类
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        self.toolbox = base.Toolbox()
        
        # 注册生成器
        bounds = self.param_space.get_bounds()
        
        def create_individual():
            """创建随机个体"""
            return creator.Individual(
                [np.random.uniform(low, high) for low, high in bounds]
            )
        
        self.toolbox.register("individual", create_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # 评估函数
        def evaluate(individual):
            """评估个体"""
            params = np.array(individual)
            # 确保参数在界内
            params = self.param_space.clip(params)
            value = self.objective(params)
            return (value,)
        
        self.toolbox.register("evaluate", evaluate)
        
        # 选择、交叉、变异算子
        self.toolbox.register(
            "select",
            tools.selTournament,
            tournsize=self.tournament_size
        )
        
        self.toolbox.register(
            "mate",
            tools.cxSimulatedBinaryBounded,
            low=[b[0] for b in bounds],
            up=[b[1] for b in bounds],
            eta=self.eta_crossover
        )
        
        self.toolbox.register(
            "mutate",
            tools.mutPolynomialBounded,
            low=[b[0] for b in bounds],
            up=[b[1] for b in bounds],
            eta=self.eta_mutation,
            indpb=1.0/len(bounds)
        )
    
    def optimize(
        self,
        n_generations: int = 100,
        verbose: bool = True,
        callback: Optional[Callable] = None
    ) -> np.ndarray:
        """
        执行遗传算法优化
        
        Args:
            n_generations: 进化代数
            verbose: 是否打印进度
            callback: 每代后的回调函数
            
        Returns:
            最优参数
        """
        # 初始化种群
        population = self.toolbox.population(n=self.population_size)

        # 热启动：用已知最优个体替换初始种群并直接赋予已知适应度，
        # 这些个体（及其未变异克隆）不再消耗 COMSOL 评估
        if self.seed_points:
            seeds = self.seed_points[: self.population_size]
            for individual, (seed_params, seed_error) in zip(population, seeds):
                clipped = self.param_space.clip(
                    np.asarray(seed_params, dtype=float)
                )
                individual[:] = [float(v) for v in clipped]
                individual.fitness.values = (float(seed_error),)
            print(
                f"[WarmStart] Seeded {len(seeds)}/{self.population_size} initial "
                f"individuals from prior trace (best seed error="
                f"{min(err for _, err in seeds):.6f})"
            )
        
        # 统计信息
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min", np.min)
        stats.register("mean", np.mean)
        stats.register("std", np.std)
        
        # Hall of Fame - 记录最优个体
        hof = tools.HallOfFame(1)
        
        if verbose:
            print(f"开始遗传算法优化 (种群大小={self.population_size}, 代数={n_generations})")
        
        # 进化
        for gen in range(n_generations):
            # 选择下一代
            offspring = self.toolbox.select(population, len(population))
            offspring = list(map(self.toolbox.clone, offspring))
            
            # 交叉和变异
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if np.random.random() < self.crossover_prob:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values
            
            for mutant in offspring:
                if np.random.random() < self.mutation_prob:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values
            
            # 评估需要评估的个体
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # 替换种群
            population[:] = offspring
            
            # 更新Hall of Fame
            hof.update(population)
            
            # 记录统计
            record = stats.compile(population)
            self.history['best'].append(record['min'])
            self.history['mean'].append(record['mean'])
            self.history['std'].append(record['std'])
            
            if verbose and (gen + 1) % 10 == 0:
                print(f"代数 {gen+1}/{n_generations}: "
                      f"最优={record['min']:.6f}, "
                      f"平均={record['mean']:.6f}, "
                      f"标准差={record['std']:.6f}")
            
            if callback:
                best_ind = hof[0]
                callback(np.array(best_ind), record['min'])
        
        # 返回最优个体
        best_individual = hof[0]
        best_params = np.array(best_individual)
        
        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {best_individual.fitness.values[0]:.6f}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), best_params):
                print(f"  {name}: {value:.6f}")
        
        return best_params
    
    def get_convergence_data(self):
        """获取收敛曲线数据"""
        return {
            'generations': np.arange(len(self.history['best'])),
            'best': np.array(self.history['best']),
            'mean': np.array(self.history['mean']),
            'std': np.array(self.history['std'])
        }


class DifferentialEvolution:
    """
    差分进化算法
    
    一种简单但强大的进化算法变体，特别适合连续优化。
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        population_size: int = 50,
        F: float = 0.8,  # 差分权重
        CR: float = 0.9,  # 交叉概率
        strategy: str = 'best1bin',
        random_state: Optional[int] = None
    ):
        """
        初始化差分进化算法
        
        Args:
            param_space: 参数空间
            objective: 目标函数
            population_size: 种群大小
            F: 差分权重（通常0.5-1.0）
            CR: 交叉概率（通常0.8-1.0）
            strategy: 进化策略
            random_state: 随机种子
        """
        self.param_space = param_space
        self.objective = objective
        self.population_size = population_size
        self.F = F
        self.CR = CR
        self.strategy = strategy
        
        if random_state is not None:
            np.random.seed(random_state)
        
        self.history = []
    
    def optimize(
        self,
        n_generations: int = 100,
        verbose: bool = True
    ) -> np.ndarray:
        """
        执行差分进化优化
        
        Args:
            n_generations: 进化代数
            verbose: 是否打印进度
            
        Returns:
            最优参数
        """
        from scipy.optimize import differential_evolution
        
        bounds = self.param_space.get_bounds()
        
        def callback_func(xk, convergence):
            """回调函数"""
            if verbose:
                print(f"当前最优值: {self.objective.best_value:.6f}")
            return False
        
        result = differential_evolution(
            func=self.objective,
            bounds=bounds,
            strategy=self.strategy,
            maxiter=n_generations,
            popsize=self.population_size // len(bounds),  # scipy的popsize是相对于维度的
            mutation=self.F,
            recombination=self.CR,
            callback=callback_func if verbose else None,
            disp=verbose
        )
        
        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {result.fun:.6f}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), result.x):
                print(f"  {name}: {value:.6f}")
        
        return result.x


