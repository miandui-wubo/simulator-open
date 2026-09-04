"""贝叶斯优化 - 最适合昂贵的仿真评估"""

import numpy as np
from typing import Optional, Callable
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.parameter_space import ParameterSpace
from src.core.objective import BaseObjective


class BayesianOptimizer:
    """
    贝叶斯优化器
    
    使用高斯过程作为代理模型，通过采集函数（acquisition function）
    平衡探索和利用，特别适合评估成本高昂的黑盒函数优化。
    
    优点：
    - 样本效率高（evaluation-efficient）
    - 自动平衡探索与利用
    - 提供不确定性估计
    
    适用场景：
    - MD/FEM仿真（每次评估需要数分钟到数小时）
    - 参数维度较低（< 20维）
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        n_initial_points: int = 10,
        acquisition_func: str = 'EI',  # 'EI', 'PI', 'LCB'
        xi: float = 0.01,
        kappa: float = 1.96,
        random_state: Optional[int] = None
    ):
        """
        初始化贝叶斯优化器
        
        Args:
            param_space: 参数空间
            objective: 目标函数
            n_initial_points: 初始随机采样点数
            acquisition_func: 采集函数类型
                - 'EI': Expected Improvement
                - 'PI': Probability of Improvement  
                - 'LCB': Lower Confidence Bound
            xi: EI/PI的exploration-exploitation权衡参数
            kappa: LCB的exploration-exploitation权衡参数
            random_state: 随机种子
        """
        self.param_space = param_space
        self.objective = objective
        self.n_initial_points = n_initial_points
        self.acquisition_func = acquisition_func
        self.xi = xi
        self.kappa = kappa
        self.random_state = random_state
        
        # 创建优化空间
        self.search_space = [
            Real(p.lower_bound, p.upper_bound, name=p.name)
            for p in param_space.parameters
        ]
        
        self.result = None
        self.history = []
    
    def optimize(
        self,
        n_iterations: int = 50,
        verbose: bool = True,
        callback: Optional[Callable] = None
    ) -> np.ndarray:
        """
        执行贝叶斯优化
        
        Args:
            n_iterations: 总迭代次数
            verbose: 是否打印进度
            callback: 每次迭代后的回调函数
            
        Returns:
            最优参数
        """
        
        @use_named_args(self.search_space)
        def objective_wrapper(**params):
            """包装目标函数以使用命名参数"""
            param_array = self.param_space.dict_to_array(params)
            value = self.objective(param_array)
            
            if verbose:
                print(f"Iteration {self.objective.n_evaluations}: f = {value:.6f}")
            
            if callback:
                callback(param_array, value)
            
            return value
        
        # 运行高斯过程优化
        # 确保初始点数至少为1，且不超过总迭代次数
        n_initial = max(1, min(self.n_initial_points, n_iterations - 1))
        if n_initial >= n_iterations:
            n_initial = max(1, n_iterations // 2)

        self.result = gp_minimize(
            func=objective_wrapper,
            dimensions=self.search_space,
            n_calls=n_iterations,
            n_initial_points=n_initial,
            acq_func=self.acquisition_func,
            xi=self.xi,
            kappa=self.kappa,
            random_state=self.random_state,
            verbose=verbose
        )
        
        # 转换结果为数组
        best_params = np.array(self.result.x)
        
        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {self.result.fun:.6f}")
            print(f"最优参数:")
            for name, value in zip(self.param_space.get_param_names(), best_params):
                print(f"  {name}: {value:.6f}")
        
        return best_params
    
    def get_convergence_plot_data(self):
        """获取收敛曲线数据"""
        if self.result is None:
            return None
        
        # 计算累积最小值
        func_vals = self.result.func_vals
        cumulative_min = np.minimum.accumulate(func_vals)
        
        return {
            'iterations': np.arange(len(func_vals)),
            'values': func_vals,
            'cumulative_min': cumulative_min
        }
    
    def get_acquisition_values(self, n_samples: int = 1000):
        """
        在参数空间中采样并计算采集函数值
        用于可视化采集函数的行为
        """
        if self.result is None or self.result.models is None:
            return None
        
        # 在参数空间中随机采样
        samples = self.param_space.sample(n_samples)
        
        # 这里需要访问skopt的内部模型来计算采集函数值
        # 简化版本：返回模型的预测均值和方差
        from skopt.acquisition import gaussian_ei
        
        model = self.result.models[-1]
        
        # 计算预测
        mu, sigma = model.predict(samples, return_std=True)
        
        # 计算采集函数值
        current_best = np.min(self.result.func_vals)
        acq_values = gaussian_ei(samples, model, y_opt=current_best, xi=self.xi)
        
        return {
            'samples': samples,
            'mean': mu,
            'std': sigma,
            'acquisition': acq_values
        }


class TPEOptimizer:
    """
    Tree-structured Parzen Estimator (TPE) 优化器
    
    另一种流行的贝叶斯优化方法，使用Parzen窗估计器
    而不是高斯过程。对高维问题表现更好。
    """
    
    def __init__(
        self,
        param_space: ParameterSpace,
        objective: BaseObjective,
        n_startup_trials: int = 10,
        random_state: Optional[int] = None
    ):
        """
        初始化TPE优化器
        
        Args:
            param_space: 参数空间
            objective: 目标函数
            n_startup_trials: 初始随机试验次数
            random_state: 随机种子
        """
        self.param_space = param_space
        self.objective = objective
        self.n_startup_trials = n_startup_trials
        self.random_state = random_state
        
        try:
            import optuna
            self.optuna = optuna
        except ImportError:
            raise ImportError("TPE需要optuna库。请运行: pip install optuna")
    
    def optimize(
        self,
        n_iterations: int = 50,
        verbose: bool = True
    ) -> np.ndarray:
        """
        执行TPE优化
        
        Args:
            n_iterations: 迭代次数
            verbose: 是否打印进度
            
        Returns:
            最优参数
        """
        
        def objective_wrapper(trial):
            """Optuna目标函数"""
            params = []
            for p in self.param_space.parameters:
                if p.scale == 'log':
                    value = trial.suggest_float(
                        p.name, p.lower_bound, p.upper_bound, log=True
                    )
                else:
                    value = trial.suggest_float(
                        p.name, p.lower_bound, p.upper_bound
                    )
                params.append(value)
            
            param_array = np.array(params)
            return self.objective(param_array)
        
        # 创建study
        sampler = self.optuna.samplers.TPESampler(
            n_startup_trials=self.n_startup_trials,
            seed=self.random_state
        )
        
        study = self.optuna.create_study(
            direction='minimize',
            sampler=sampler
        )
        
        # 优化
        study.optimize(
            objective_wrapper,
            n_trials=n_iterations,
            show_progress_bar=verbose
        )
        
        # 提取最优参数
        best_params = np.array([
            study.best_params[p.name]
            for p in self.param_space.parameters
        ])
        
        if verbose:
            print(f"\n优化完成!")
            print(f"最优值: {study.best_value:.6f}")
            print(f"最优参数:")
            for name, value in study.best_params.items():
                print(f"  {name}: {value:.6f}")
        
        self.study = study
        return best_params


