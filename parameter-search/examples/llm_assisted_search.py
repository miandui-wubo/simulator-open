"""LLM辅助搜索示例"""

import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.parameter_space import create_thermodynamic_parameter_space
from src.core.objective import MockObjective
from src.llm.llm_optimizer import LLMOptimizer
from src.optimizers.bayesian_optimizer import BayesianOptimizer
import matplotlib.pyplot as plt


def main():
    """运行LLM辅助搜索示例"""
    
    print("=" * 60)
    print("LLM辅助参数搜索示例")
    print("=" * 60)
    
    # 1. 创建参数空间
    param_space = create_thermodynamic_parameter_space()
    print(f"\n参数空间：\n{param_space}")
    
    # 2. 创建目标函数
    objective = MockObjective(dimension=len(param_space), noise_level=0.01)
    
    # 3. 检查API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key is None:
        print("\n警告：未找到OPENAI_API_KEY环境变量")
        print("LLM功能将受限，将使用随机策略代替")
        print("\n如需使用LLM功能，请设置环境变量：")
        print("  export OPENAI_API_KEY='your-api-key'")
    else:
        print(f"\n✓ 已找到API密钥")
    
    # 4. 创建LLM优化器
    print(f"\n{'='*60}")
    print("初始化LLM辅助优化器")
    print(f"{'='*60}")
    
    llm_optimizer = LLMOptimizer(
        param_space=param_space,
        objective=objective,
        model="gpt-4",  # 或 "gpt-3.5-turbo"
        use_knowledge_base=True
    )
    
    # 5. 运行优化
    print(f"\n开始LLM辅助优化...")
    
    best_params = llm_optimizer.optimize(
        n_iterations=30,
        n_random_init=5,
        check_reasonableness=True,  # 启用物理合理性检查
        verbose=True
    )
    
    # 6. 诊断收敛状况
    print(f"\n{'='*60}")
    print("收敛诊断")
    print(f"{'='*60}")
    
    if api_key:
        diagnosis = llm_optimizer.diagnose_convergence()
        print(f"\nLLM诊断结果:")
        print(f"  状态: {diagnosis.get('convergence_status', 'unknown')}")
        print(f"  是否局部最优: {diagnosis.get('is_local_optimum', 'unknown')}")
        
        if 'recommendations' in diagnosis:
            print(f"\n建议:")
            for rec in diagnosis['recommendations']:
                print(f"  - {rec}")
    
    # 7. 结果总结
    print(f"\n{'='*60}")
    print("优化结果")
    print(f"{'='*60}")
    
    print(f"\n最优值: {llm_optimizer.best_value:.6f}")
    print(f"总评估次数: {len(llm_optimizer.evaluation_history)}")
    
    print(f"\n最优参数:")
    for name, value in zip(param_space.get_param_names(), best_params):
        print(f"  {name}: {value:.6f}")
    
    # 8. 与传统方法对比
    print(f"\n{'='*60}")
    print("与传统贝叶斯优化对比")
    print(f"{'='*60}")
    
    objective_bo = MockObjective(dimension=len(param_space), noise_level=0.01)
    bo_optimizer = BayesianOptimizer(
        param_space=param_space,
        objective=objective_bo,
        n_initial_points=5
    )
    
    best_params_bo = bo_optimizer.optimize(n_iterations=30, verbose=False)
    
    print(f"\n{'方法':<30} {'最优值':<15} {'评估次数':<15}")
    print("-" * 60)
    print(f"{'LLM辅助优化':<30} {llm_optimizer.best_value:<15.6f} {len(llm_optimizer.evaluation_history):<15}")
    print(f"{'贝叶斯优化':<30} {objective_bo.best_value:<15.6f} {objective_bo.n_evaluations:<15}")
    
    print(f"\n{'='*60}")
    print("LLM辅助搜索示例完成!")
    print(f"{'='*60}")
    
    print(f"\n提示:")
    print(f"  - LLM可以利用物理知识指导搜索")
    print(f"  - 可以检测不合理的参数组合")
    print(f"  - 提供可解释的搜索策略")
    print(f"  - 适合结合领域知识的复杂优化问题")


if __name__ == "__main__":
    main()


