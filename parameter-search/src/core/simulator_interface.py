"""仿真器接口 - 连接优化器和实际仿真程序"""

import numpy as np
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import subprocess
import json
import tempfile
import os


class BaseSimulator(ABC):
    """仿真器基类"""
    
    @abstractmethod
    def run(self, params: Dict[str, float]) -> Dict[str, np.ndarray]:
        """
        运行仿真
        
        Args:
            params: 参数字典
            
        Returns:
            观测量字典
        """
        pass
    
    @abstractmethod
    def setup(self):
        """设置仿真环境"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理仿真环境"""
        pass


class LAMMPSSimulator(BaseSimulator):
    """
    LAMMPS分子动力学仿真器接口
    
    适用于液态金属MD模拟
    """
    
    def __init__(
        self,
        lammps_executable: str = "lmp",
        template_file: str = "input.template",
        work_dir: Optional[str] = None
    ):
        """
        初始化LAMMPS仿真器
        
        Args:
            lammps_executable: LAMMPS可执行文件路径
            template_file: 输入文件模板
            work_dir: 工作目录
        """
        self.lammps_executable = lammps_executable
        self.template_file = template_file
        self.work_dir = work_dir or tempfile.mkdtemp()
    
    def setup(self):
        """设置仿真环境"""
        os.makedirs(self.work_dir, exist_ok=True)
    
    def run(self, params: Dict[str, float]) -> Dict[str, np.ndarray]:
        """
        运行LAMMPS仿真
        
        Args:
            params: 力场参数
            
        Returns:
            计算的物理量（密度、扩散系数、粘度等）
        """
        # 1. 生成输入文件
        input_file = self._generate_input_file(params)
        
        # 2. 运行LAMMPS
        try:
            result = subprocess.run(
                [self.lammps_executable, "-in", input_file],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"LAMMPS运行失败: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("LAMMPS运行超时")
        
        # 3. 解析输出
        observables = self._parse_output()
        
        return observables
    
    def _generate_input_file(self, params: Dict[str, float]) -> str:
        """生成LAMMPS输入文件"""
        # 读取模板
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # 替换参数
        for param_name, param_value in params.items():
            placeholder = f"${{{param_name}}}"
            template = template.replace(placeholder, str(param_value))
        
        # 写入工作目录
        input_file = os.path.join(self.work_dir, "input.lammps")
        with open(input_file, 'w') as f:
            f.write(template)
        
        return input_file
    
    def _parse_output(self) -> Dict[str, np.ndarray]:
        """解析LAMMPS输出"""
        # 这里需要根据实际的LAMMPS输出格式解析
        # 简化示例
        observables = {
            'density': np.array([]),
            'msd': np.array([]),
            'viscosity': np.array([])
        }
        
        # 实际实现应该读取log文件和数据文件
        return observables
    
    def cleanup(self):
        """清理临时文件"""
        import shutil
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)


class LAMMPSWorkflowSimulator(BaseSimulator):
    """
    基于已有工作流脚本的LAMMPS调用器

    参考用户提供的流程：
    1) 调用 lammps_calculate(lammps_input) 生成并运行 LAMMPS 输入
    2) 调用 log_analyze(lammps_input) 解析 log，返回结果
    3) 也支持直接 shell 调用: cd workdir && lmp -in input_file
    """

    def __init__(
        self,
        work_dir: str,
        input_file: str = "in.lammps",
        lammps_executable: str = "lmp",
        runner: Optional[Callable[[str], bool]] = None,
        parser: Optional[Callable[[str], Dict[str, Any]]] = None,
    ):
        """
        Args:
            work_dir: LAMMPS 工作目录（包含 in 文件）
            input_file: LAMMPS 输入文件名
            lammps_executable: LAMMPS 可执行文件
            runner: 可选，自定义的 lammps_calculate(lammps_input) 函数
            parser: 可选，自定义的 log_analyze(lammps_input) 函数，需返回观测量字典
        """
        self.work_dir = work_dir
        self.input_file = input_file
        self.lammps_executable = lammps_executable
        self.runner = runner
        self.parser = parser

    def setup(self):
        """外部工作目录由用户维护，这里不做处理"""
        pass

    def cleanup(self):
        """外部工作目录由用户维护，这里不做处理"""
        pass

    def run(self, params: Dict[str, float]) -> Dict[str, np.ndarray]:
        """
        运行仿真：
        - 如果提供 runner/parser，则按用户工作流调用
        - 否则直接 shell 调用 lmp -in
        """
        # 将参数序列化为字符串，传给外部工作流（可按需调整）
        lammps_input = json.dumps(params)

        if self.runner and self.parser:
            ok = self.runner(lammps_input)
            if not ok:
                raise RuntimeError("LAMMPS calculation failed after all retries.")
            result = self.parser(lammps_input)
            return self._to_numpy(result)

        # 直接调用 lmp -in
        cmd = f'cd "{self.work_dir}" && {self.lammps_executable} -in {self.input_file}'
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                timeout=3600,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LAMMPS运行失败: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("LAMMPS运行超时")

        # 如果提供 parser，仅解析；否则返回空结果，由上层决定如何处理
        if self.parser:
            result = self.parser(lammps_input)
            return self._to_numpy(result)

        # 没有解析器时，返回空观测量，避免崩溃
        return {}

    @staticmethod
    def _to_numpy(result: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """将解析结果中的标量/列表转换为 numpy 数组，便于统一处理"""
        obs = {}
        for k, v in result.items():
            if isinstance(v, np.ndarray):
                obs[k] = v
            elif isinstance(v, (list, tuple)):
                obs[k] = np.array(v)
            else:
                obs[k] = np.array([v])
        return obs

class MockSimulator(BaseSimulator):
    """
    模拟仿真器（用于测试和演示）
    
    使用解析函数模拟真实仿真过程
    """
    
    def __init__(
        self,
        n_observables: int = 3,
        noise_level: float = 0.05,
        computation_time: float = 0.1
    ):
        """
        初始化模拟仿真器
        
        Args:
            n_observables: 观测量数量
            noise_level: 噪声水平
            computation_time: 模拟计算时间（秒）
        """
        self.n_observables = n_observables
        self.noise_level = noise_level
        self.computation_time = computation_time
        
        # 生成"真实"参数
        self.true_params = None
    
    def setup(self):
        """设置"""
        pass
    
    def set_true_params(self, true_params: Dict[str, float]):
        """设置真实参数（用于生成实验数据）"""
        self.true_params = true_params
    
    def run(self, params: Dict[str, float]) -> Dict[str, np.ndarray]:
        """
        模拟运行
        
        生成与参数相关的观测量
        """
        import time
        time.sleep(self.computation_time)
        
        # 将参数转换为数组
        param_array = np.array(list(params.values()))
        
        # 生成观测量
        observables = {}
        
        for i in range(self.n_observables):
            # 使用简单的非线性函数模拟观测量与参数的关系
            observable = self._compute_observable(param_array, i)
            
            # 添加噪声
            noise = np.random.normal(0, self.noise_level * np.abs(observable))
            observable += noise
            
            observables[f'observable_{i}'] = np.array([observable])
        
        return observables
    
    def _compute_observable(self, params: np.ndarray, obs_idx: int) -> float:
        """计算观测量"""
        # 简单的非线性函数
        # 实际应该是基于物理模型的复杂函数
        
        # 示例：不同观测量对不同参数的依赖
        if obs_idx == 0:
            # 密度：主要依赖于前几个参数
            value = np.sum(params[:3]**2)
        elif obs_idx == 1:
            # 扩散系数：依赖于温度相关参数
            value = np.exp(-params[0]) * np.sum(params[3:6])
        else:
            # 其他：复杂的非线性关系
            value = np.sum(np.sin(params) * np.cos(params[::-1]))
        
        return value
    
    def cleanup(self):
        """清理"""
        pass


def create_experimental_data(
    simulator: BaseSimulator,
    true_params: Dict[str, float],
    n_measurements: int = 1
) -> Dict[str, np.ndarray]:
    """
    使用"真实"参数生成实验数据
    
    Args:
        simulator: 仿真器
        true_params: 真实参数
        n_measurements: 测量次数（用于平均）
        
    Returns:
        实验数据字典
    """
    all_measurements = []
    
    for _ in range(n_measurements):
        measurement = simulator.run(true_params)
        all_measurements.append(measurement)
    
    # 平均多次测量
    experimental_data = {}
    for obs_name in all_measurements[0].keys():
        values = [m[obs_name] for m in all_measurements]
        experimental_data[obs_name] = np.mean(values, axis=0)
    
    return experimental_data


