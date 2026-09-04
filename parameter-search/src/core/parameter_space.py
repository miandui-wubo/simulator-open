"""参数空间定义模块"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field


@dataclass
class Parameter:
    """单个参数定义"""
    name: str
    lower_bound: float
    upper_bound: float
    scale: str = 'linear'  # 'linear' or 'log'
    unit: Optional[str] = None
    description: Optional[str] = None
    physical_meaning: Optional[str] = None
    
    def sample(self, n: int = 1) -> np.ndarray:
        """在参数范围内采样"""
        if self.scale == 'log':
            samples = np.exp(np.random.uniform(
                np.log(self.lower_bound),
                np.log(self.upper_bound),
                n
            ))
        else:
            samples = np.random.uniform(self.lower_bound, self.upper_bound, n)
        return samples
    
    def normalize(self, value: float) -> float:
        """将参数值归一化到[0,1]"""
        if self.scale == 'log':
            return (np.log(value) - np.log(self.lower_bound)) / \
                   (np.log(self.upper_bound) - np.log(self.lower_bound))
        else:
            return (value - self.lower_bound) / (self.upper_bound - self.lower_bound)
    
    def denormalize(self, normalized_value: float) -> float:
        """将归一化值转换回原始尺度"""
        if self.scale == 'log':
            return np.exp(
                normalized_value * (np.log(self.upper_bound) - np.log(self.lower_bound)) +
                np.log(self.lower_bound)
            )
        else:
            return normalized_value * (self.upper_bound - self.lower_bound) + self.lower_bound


class ParameterSpace:
    """参数空间管理类"""
    
    def __init__(self, parameters: Union[Dict[str, Tuple], List[Parameter]]):
        """
        初始化参数空间
        
        Args:
            parameters: 可以是字典 {'name': (lower, upper)} 或 Parameter列表
        """
        if isinstance(parameters, dict):
            self.parameters = [
                Parameter(name=name, lower_bound=bounds[0], upper_bound=bounds[1])
                for name, bounds in parameters.items()
            ]
        else:
            self.parameters = parameters
        
        self.param_dict = {p.name: p for p in self.parameters}
        self.dimension = len(self.parameters)
    
    def sample(self, n: int = 1) -> np.ndarray:
        """
        在参数空间中采样
        
        Args:
            n: 采样数量
            
        Returns:
            shape (n, dim) 的参数数组
        """
        samples = np.array([param.sample(n) for param in self.parameters]).T
        return samples
    
    def normalize(self, params: Union[np.ndarray, Dict[str, float]]) -> np.ndarray:
        """归一化参数到[0,1]^d"""
        if isinstance(params, dict):
            params = np.array([params[p.name] for p in self.parameters])
        
        normalized = np.array([
            self.parameters[i].normalize(params[i])
            for i in range(self.dimension)
        ])
        return normalized
    
    def denormalize(self, normalized_params: np.ndarray) -> np.ndarray:
        """反归一化参数"""
        return np.array([
            self.parameters[i].denormalize(normalized_params[i])
            for i in range(self.dimension)
        ])
    
    def get_bounds(self) -> List[Tuple[float, float]]:
        """获取所有参数的边界"""
        return [(p.lower_bound, p.upper_bound) for p in self.parameters]
    
    def get_param_names(self) -> List[str]:
        """获取参数名称列表"""
        return [p.name for p in self.parameters]
    
    def array_to_dict(self, param_array: np.ndarray) -> Dict[str, float]:
        """将参数数组转换为字典"""
        return {p.name: param_array[i] for i, p in enumerate(self.parameters)}
    
    def dict_to_array(self, param_dict: Dict[str, float]) -> np.ndarray:
        """将参数字典转换为数组"""
        return np.array([param_dict[p.name] for p in self.parameters])
    
    def clip(self, params: np.ndarray) -> np.ndarray:
        """将参数裁剪到合法范围"""
        clipped = params.copy()
        for i, p in enumerate(self.parameters):
            clipped[i] = np.clip(clipped[i], p.lower_bound, p.upper_bound)
        return clipped
    
    def __len__(self) -> int:
        return self.dimension
    
    def __repr__(self) -> str:
        info = f"ParameterSpace(dimension={self.dimension})\n"
        for p in self.parameters:
            info += f"  {p.name}: [{p.lower_bound}, {p.upper_bound}]"
            if p.unit:
                info += f" {p.unit}"
            info += "\n"
        return info


# 预定义的材料参数空间示例
def create_thermodynamic_parameter_space() -> ParameterSpace:
    """创建典型的液态金属合金热力学参数空间（10个参数）"""
    parameters = [
        Parameter(
            name='cohesive_energy',
            lower_bound=3.0,
            upper_bound=5.0,
            unit='eV',
            description='Cohesive energy',
            physical_meaning='原子间结合能'
        ),
        Parameter(
            name='lattice_constant',
            lower_bound=3.5,
            upper_bound=4.5,
            unit='Å',
            description='Lattice constant',
            physical_meaning='晶格常数'
        ),
        Parameter(
            name='bulk_modulus',
            lower_bound=80.0,
            upper_bound=150.0,
            unit='GPa',
            description='Bulk modulus',
            physical_meaning='体积模量'
        ),
        Parameter(
            name='shear_modulus',
            lower_bound=30.0,
            upper_bound=80.0,
            unit='GPa',
            description='Shear modulus',
            physical_meaning='剪切模量'
        ),
        Parameter(
            name='surface_energy',
            lower_bound=1.0,
            upper_bound=3.0,
            unit='J/m²',
            description='Surface energy',
            physical_meaning='表面能'
        ),
        Parameter(
            name='melting_temperature',
            lower_bound=900.0,
            upper_bound=1400.0,
            unit='K',
            description='Melting temperature',
            physical_meaning='熔点'
        ),
        Parameter(
            name='thermal_expansion_coeff',
            lower_bound=10.0,
            upper_bound=30.0,
            scale='linear',
            unit='10⁻⁶/K',
            description='Thermal expansion coefficient',
            physical_meaning='热膨胀系数'
        ),
        Parameter(
            name='heat_capacity',
            lower_bound=20.0,
            upper_bound=35.0,
            unit='J/(mol·K)',
            description='Heat capacity',
            physical_meaning='热容'
        ),
        Parameter(
            name='diffusion_coefficient',
            lower_bound=1e-9,
            upper_bound=1e-7,
            scale='log',
            unit='m²/s',
            description='Diffusion coefficient',
            physical_meaning='扩散系数'
        ),
        Parameter(
            name='viscosity',
            lower_bound=1e-3,
            upper_bound=1e-1,
            scale='log',
            unit='Pa·s',
            description='Viscosity',
            physical_meaning='粘度'
        )
    ]
    
    return ParameterSpace(parameters)


