"""
Configuration for the integrated simulation pipeline.

Defines the input [A]: target contact angles, fixed material parameters,
and search parameter bounds.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional


@dataclass
class MaterialConfig:
    """Fixed material configuration (part of [C])."""
    droplet_name: str = "Ga"
    left_substrate_name: str = "Si"
    right_substrate_name: str = "GaN"
    mesh_fineness: int = 4


@dataclass
class LLMCodegenConfig:
    """Settings for one-time local LLM code generation."""
    enabled: bool = False
    model_dir: str = "./comsol_work/model/matlab_checkpoint-39"
    prompt_path: str = "./simulator/prompt/matlab_param_template_prompt.md"
    cache_path: str = "./simulation_workspace/llm_cache/param_code_template.m"
    allow_fallback_template: bool = False
    timeout_seconds: int = 600


@dataclass
class SimulationConfig:
    """
    Full simulation configuration [A].

    Contains:
    - target_left_contact_angle / target_right_contact_angle: experimental values to match
    - material: fixed material names / mesh settings [C]
    - search_bounds: parameter name → (lower, upper) for the optimizer
    - tolerance_deg: acceptable error in degrees
    """
    target_left_contact_angle: float = 27.27
    target_right_contact_angle: float = 13.43

    material: MaterialConfig = field(default_factory=MaterialConfig)

    search_bounds: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "surface_tension": (0.1, 0.8),
        "droplet_density": (5000.0, 7000.0),
        "droplet_viscosity": (0.001, 0.01),
        "left_substrate_density": (2000.0, 3000.0),
        "left_substrate_heat_capacity": (500.0, 900.0),
        "left_substrate_thermal_conductivity": (100.0, 200.0),
        "right_substrate_density": (5000.0, 7000.0),
        "right_substrate_heat_capacity": (400.0, 700.0),
        "right_substrate_thermal_conductivity": (100.0, 200.0),
        "left_substrate_temperature": (293.15, 323.15),
        "right_substrate_temperature": (343.15, 393.15),
        "left_contact_angle": (20.0, 35.0),
        "right_contact_angle": (10.0, 20.0),
    })

    tolerance_deg: float = 1.0
    max_iterations: int = 50
    optimizer: str = "bayesian"

    comsol_bin_dir: Optional[str] = r"C:\Program Files\COMSOL\COMSOL61\Multiphysics\bin\win64"
    comsol_mli_dir: Optional[str] = r"C:\Program Files\COMSOL\COMSOL61\Multiphysics\mli"
    # Per-eval MATLAB/COMSOL wall time (workspace logs: 1800s was too low; raised to 7200s).
    comsol_timeout_seconds: int = 7200
    max_consecutive_failures: int = 20
    work_dir: str = "./simulation_workspace"
    use_mock: bool = False  # Default to real COMSOL if available
    llm_codegen: LLMCodegenConfig = field(default_factory=LLMCodegenConfig)


def create_default_config() -> SimulationConfig:
    """Create a default configuration for Ga on Si/GaN."""
    return SimulationConfig()


def create_config_from_dict(d: dict) -> SimulationConfig:
    """Build a SimulationConfig from a flat dictionary (e.g. loaded from YAML)."""
    mat_keys = {"droplet_name", "left_substrate_name", "right_substrate_name", "mesh_fineness"}
    mat_dict = {k: d[k] for k in mat_keys if k in d}
    material = MaterialConfig(**mat_dict) if mat_dict else MaterialConfig()

    cfg_keys = {
        "target_left_contact_angle", "target_right_contact_angle",
        "tolerance_deg", "max_iterations", "optimizer",
        "comsol_bin_dir", "comsol_mli_dir", "comsol_timeout_seconds",
        "max_consecutive_failures", "work_dir", "use_mock",
    }
    cfg_dict = {k: d[k] for k in cfg_keys if k in d}

    if "search_bounds" in d:
        cfg_dict["search_bounds"] = {
            k: tuple(v) for k, v in d["search_bounds"].items()
        }

    llm_dict = d.get("llm_codegen")
    if isinstance(llm_dict, dict):
        cfg_dict["llm_codegen"] = LLMCodegenConfig(**llm_dict)

    return SimulationConfig(material=material, **cfg_dict)
