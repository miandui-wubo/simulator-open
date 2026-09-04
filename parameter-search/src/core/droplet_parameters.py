"""液滴实验参数空间定义

根据用户提供的13个参数定义参数空间
包括参考值（来自文献）用于辅助搜索
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.core.parameter_space import Parameter, ParameterSpace


@dataclass
class ReferenceValue:
    """参数参考值（来自文献或数据库）"""
    material: str
    value: float
    source: str
    confidence: float = 0.5  # 置信度 0-1


# =============================================================================
# 参考值数据（来自第二张图片）
# =============================================================================

REFERENCE_DATA = {
    # 液滴材料参考值
    'droplet': {
        'Ga': {
            'density': 5907,           # kg/m³
            'dynamic_viscosity': 1.87e-3,  # Pa·s (1.87×10^-4 mPa·s = 1.87×10^-3 Pa·s)
            'surface_tension': 0.5,    # N/m
        },
        'GaIn': {
            'density': 6250,           # kg/m³ (at 25°C)
            'dynamic_viscosity': 2e-3, # Pa·s (2~4×10^-3 Pa·s)
            'surface_tension': 0.624,  # N/m
        },
        'GaInSn': {
            'density': 6440,           # kg/m³
            'dynamic_viscosity': 2.4e-3,  # Pa·s (0.0024 Pa·s at 20°C)
            'surface_tension': 0.718,  # N/m
        },
    },
    # 基板材料参考值
    'substrate': {
        'Si': {
            'density': 2329,           # kg/m³
            'thermal_conductivity': 150,  # W/(m·K)
            'heat_capacity': 710,      # J/(kg·K)
        },
        'GaN': {
            'density': 5800,           # kg/m³ (5.5-6.1 g/cm³)
            'thermal_conductivity': 130,  # W/(m·K) (1.3 W/cmK = 130 W/mK)
            'heat_capacity': 600,      # J/(kg·K) - 估计值
        },
        'GaAs': {
            'density': 5316,           # kg/m³
            'thermal_conductivity': 55,   # W/(m·K) (0.167 W/cm/°C ≈ 16.7 W/mK)
            'heat_capacity': 330,      # J/(kg·K) - 估计值
        },
    }
}


def create_droplet_experiment_parameter_space() -> ParameterSpace:
    """
    创建液滴实验的参数空间（13个参数）
    
    参数来源：用户提供的第一张图片
    """
    
    parameters = [
        # ===== 温度参数 =====
        Parameter(
            name='left_substrate_temperature',
            lower_bound=305.0,
            upper_bound=315.0,
            unit='K',
            description='Left substrate temperature',
            physical_meaning='左基板温度'
        ),
        Parameter(
            name='right_substrate_temperature',
            lower_bound=305.0,
            upper_bound=315.0,
            unit='K',
            description='Right substrate temperature',
            physical_meaning='右基板温度'
        ),
        
        # ===== 接触角参数 =====
        Parameter(
            name='left_contact_angle',
            lower_bound=15.0,
            upper_bound=30.0,
            unit='deg',
            description='Left substrate contact angle',
            physical_meaning='左基板接触角'
        ),
        Parameter(
            name='right_contact_angle',
            lower_bound=15.0,
            upper_bound=30.0,
            unit='deg',
            description='Right substrate contact angle',
            physical_meaning='右基板接触角'
        ),
        
        # ===== 表面张力 =====
        Parameter(
            name='surface_tension',
            lower_bound=0.1,
            upper_bound=0.5,
            unit='N/m',
            description='Surface tension',
            physical_meaning='表面张力'
        ),
        
        # ===== 基板密度 =====
        Parameter(
            name='left_substrate_density',
            lower_bound=3000.0,
            upper_bound=7000.0,
            unit='kg/m³',
            description='Left substrate density',
            physical_meaning='左基板密度'
        ),
        Parameter(
            name='right_substrate_density',
            lower_bound=300.0,
            upper_bound=700.0,
            unit='kg/m³',
            description='Right substrate density',
            physical_meaning='右基板密度'
        ),
        
        # ===== 恒压热容 =====
        Parameter(
            name='left_heat_capacity',
            lower_bound=300.0,
            upper_bound=700.0,
            unit='J/(kg·K)',
            description='Left substrate heat capacity at constant pressure',
            physical_meaning='左基板恒压热容'
        ),
        Parameter(
            name='right_heat_capacity',
            lower_bound=300.0,
            upper_bound=1000.0,
            unit='J/(kg·K)',
            description='Right substrate heat capacity at constant pressure',
            physical_meaning='右基板恒压热容'
        ),
        
        # ===== 液滴属性 =====
        Parameter(
            name='droplet_density',
            lower_bound=3000.0,
            upper_bound=7000.0,
            unit='kg/m³',
            description='Droplet density',
            physical_meaning='液滴密度'
        ),
        Parameter(
            name='droplet_viscosity',
            lower_bound=0.1,
            upper_bound=0.3,
            unit='Pa·s',
            description='Droplet dynamic viscosity',
            physical_meaning='液滴动力黏度'
        ),
        
        # ===== 导热系数 =====
        Parameter(
            name='left_thermal_conductivity',
            lower_bound=100.0,
            upper_bound=250.0,
            unit='W/(m·K)',
            description='Left substrate thermal conductivity',
            physical_meaning='左基板导热系数'
        ),
        Parameter(
            name='right_thermal_conductivity',
            lower_bound=30.0,
            upper_bound=80.0,
            unit='W/(m·K)',
            description='Right substrate thermal conductivity',
            physical_meaning='右基板导热系数'
        ),
    ]
    
    return ParameterSpace(parameters)


def get_initial_guess_from_literature(material_type: str = 'GaInSn') -> Dict[str, float]:
    """
    基于文献参考值生成初始猜测
    
    Args:
        material_type: 液滴材料类型 ('Ga', 'GaIn', 'GaInSn')
    
    Returns:
        初始参数字典
    """
    
    droplet = REFERENCE_DATA['droplet'].get(material_type, REFERENCE_DATA['droplet']['GaInSn'])
    substrate_left = REFERENCE_DATA['substrate']['Si']   # 假设左基板是Si
    substrate_right = REFERENCE_DATA['substrate']['GaN'] # 假设右基板是GaN
    
    return {
        # 温度 - 取中间值
        'left_substrate_temperature': 310.0,
        'right_substrate_temperature': 310.0,
        
        # 接触角 - 取中间值
        'left_contact_angle': 22.5,
        'right_contact_angle': 22.5,
        
        # 表面张力 - 使用文献值（需要裁剪到范围内）
        'surface_tension': min(0.5, max(0.1, droplet.get('surface_tension', 0.3))),
        
        # 基板密度 - 使用文献值（需要裁剪）
        'left_substrate_density': min(7000, max(3000, substrate_left['density'])),
        'right_substrate_density': min(700, max(300, 500)),  # 文献值超出范围，取中间
        
        # 热容
        'left_heat_capacity': min(700, max(300, substrate_left['heat_capacity'])),
        'right_heat_capacity': min(1000, max(300, substrate_right.get('heat_capacity', 600))),
        
        # 液滴属性
        'droplet_density': min(7000, max(3000, droplet['density'])),
        'droplet_viscosity': min(0.3, max(0.1, 0.2)),  # 文献值（~0.002 Pa·s）远小于范围
        
        # 导热系数
        'left_thermal_conductivity': min(250, max(100, substrate_left['thermal_conductivity'])),
        'right_thermal_conductivity': min(80, max(30, 55)),  # GaN ~130, 超出范围
    }


def print_parameter_summary(param_space: ParameterSpace):
    """打印参数摘要"""
    print("=" * 70)
    print("液滴实验参数空间摘要 (13个参数)")
    print("=" * 70)
    print(f"\n{'参数名称':<30} {'范围':<25} {'单位':<15}")
    print("-" * 70)
    
    for p in param_space.parameters:
        range_str = f"[{p.lower_bound}, {p.upper_bound}]"
        print(f"{p.physical_meaning:<30} {range_str:<25} {p.unit:<15}")
    
    print("-" * 70)
    print(f"总参数数量: {len(param_space)}")
    print("=" * 70)


def get_parameter_groups() -> Dict[str, List[str]]:
    """
    获取参数分组信息（用于分组优化或敏感性分析）
    """
    return {
        'temperature': [
            'left_substrate_temperature',
            'right_substrate_temperature'
        ],
        'contact_angle': [
            'left_contact_angle',
            'right_contact_angle'
        ],
        'left_substrate': [
            'left_substrate_density',
            'left_heat_capacity',
            'left_thermal_conductivity'
        ],
        'right_substrate': [
            'right_substrate_density',
            'right_heat_capacity',
            'right_thermal_conductivity'
        ],
        'droplet': [
            'droplet_density',
            'droplet_viscosity',
            'surface_tension'
        ]
    }


# =============================================================================
# 物理约束检查
# =============================================================================

def check_physical_constraints(params: Dict[str, float]) -> Dict[str, any]:
    """
    检查参数的物理约束
    
    Returns:
        {
            'is_valid': bool,
            'warnings': list,
            'errors': list
        }
    """
    warnings = []
    errors = []
    
    # 1. 温度检查
    if params['left_substrate_temperature'] == params['right_substrate_temperature']:
        warnings.append("左右基板温度相同，可能没有热驱动力")
    
    # 2. 接触角检查
    if params['left_contact_angle'] == params['right_contact_angle']:
        warnings.append("左右接触角相同，可能没有润湿性梯度")
    
    # 3. 表面张力与温度的关系（一般表面张力随温度升高而降低）
    # 这是一个简化的检查
    
    # 4. 密度检查
    if params['left_substrate_density'] < params['droplet_density']:
        warnings.append("左基板密度小于液滴密度，可能导致浮力效应")
    
    # 5. 热导率与热容的关系
    # 热扩散率 α = k / (ρ * Cp)
    left_diffusivity = params['left_thermal_conductivity'] / (
        params['left_substrate_density'] * params['left_heat_capacity']
    )
    right_diffusivity = params['right_thermal_conductivity'] / (
        params['right_substrate_density'] * params['right_heat_capacity']
    )
    
    if abs(left_diffusivity - right_diffusivity) < 1e-8:
        warnings.append("左右基板热扩散率相近，温度响应可能相似")
    
    return {
        'is_valid': len(errors) == 0,
        'warnings': warnings,
        'errors': errors,
        'left_thermal_diffusivity': left_diffusivity,
        'right_thermal_diffusivity': right_diffusivity
    }


# =============================================================================
# 敏感性先验知识
# =============================================================================

PARAMETER_SENSITIVITY_PRIOR = {
    # 基于物理直觉的敏感性排序（高 -> 低）
    # 这可以用来指导优化策略
    'high_sensitivity': [
        'surface_tension',           # 表面张力对液滴行为影响大
        'left_contact_angle',        # 接触角直接影响润湿
        'right_contact_angle',
        'droplet_viscosity',         # 粘度影响流动
    ],
    'medium_sensitivity': [
        'left_substrate_temperature',
        'right_substrate_temperature',
        'droplet_density',
        'left_thermal_conductivity',
        'right_thermal_conductivity',
    ],
    'low_sensitivity': [
        'left_substrate_density',
        'right_substrate_density',
        'left_heat_capacity',
        'right_heat_capacity',
    ]
}


def get_optimization_weights() -> Dict[str, float]:
    """
    基于敏感性先验获取参数权重（用于加权采样）
    
    高敏感性参数应该更细致地搜索
    """
    weights = {}
    
    for param in PARAMETER_SENSITIVITY_PRIOR['high_sensitivity']:
        weights[param] = 1.0
    
    for param in PARAMETER_SENSITIVITY_PRIOR['medium_sensitivity']:
        weights[param] = 0.7
    
    for param in PARAMETER_SENSITIVITY_PRIOR['low_sensitivity']:
        weights[param] = 0.4
    
    return weights


# =============================================================================
# 主函数（测试）
# =============================================================================

if __name__ == "__main__":
    # 创建参数空间
    param_space = create_droplet_experiment_parameter_space()
    
    # 打印摘要
    print_parameter_summary(param_space)
    
    # 获取文献初始值
    print("\n基于文献的初始猜测 (GaInSn):")
    initial_guess = get_initial_guess_from_literature('GaInSn')
    for name, value in initial_guess.items():
        print(f"  {name}: {value}")
    
    # 检查物理约束
    print("\n物理约束检查:")
    check_result = check_physical_constraints(initial_guess)
    print(f"  有效: {check_result['is_valid']}")
    if check_result['warnings']:
        print(f"  警告: {check_result['warnings']}")

