"""
Mock COMSOL simulator for testing the pipeline without a real COMSOL installation.

Generates a synthetic 3D droplet point-cloud TXT file whose contact angle
is deterministically related to the input parameters, allowing the optimizer
to converge to the correct solution.
"""

import os
import numpy as np
from typing import Dict, Optional


def _spherical_cap_points(contact_angle_deg: float,
                          radius: float = 2.0,
                          n_points: int = 3000,
                          noise: float = 0.005) -> np.ndarray:
    """
    Generate points on the iso-surface (level-set = 0.5) of a spherical cap
    with the given contact angle, sitting on the z=0 plane.

    For a sphere of radius R centered at z_c = R*cos(theta):
      - The cap extends from alpha=0 (top) to alpha=pi-theta (contact line at z=0)
      - Contact line radius: a = R*sin(theta)
      - Cap height: h = R*(1 + cos(theta)) - R*cos(theta) = R
    """
    theta_rad = np.radians(max(1.0, min(179.0, contact_angle_deg)))
    z_c = radius * np.cos(theta_rad)
    alpha_max = np.pi - theta_rad

    alpha = np.random.uniform(0, alpha_max, n_points)
    beta = np.random.uniform(0, 2 * np.pi, n_points)

    x = radius * np.sin(alpha) * np.cos(beta)
    y = radius * np.sin(alpha) * np.sin(beta)
    z = z_c + radius * np.cos(alpha)

    x += np.random.normal(0, noise, n_points)
    y += np.random.normal(0, noise, n_points)
    z += np.random.normal(0, noise, n_points)
    z = np.clip(z, 0, None)

    return np.column_stack([x, y, z])


def compute_effective_contact_angle(params: Dict[str, float]) -> float:
    """
    Compute a 'simulated' contact angle from parameters.

    In a real COMSOL simulation, the resulting contact angle depends on
    the interplay of surface tension, viscosity, substrate thermal properties,
    temperature gradients, etc.

    This mock function approximates that relationship so the optimizer
    can meaningfully search for parameters that match a target contact angle.

    The main drivers are:
    - left_contact_angle / right_contact_angle (boundary conditions)
    - surface_tension (higher → droplet tends toward equilibrium shape)
    - droplet_viscosity (higher → slower spreading → larger angle)
    - temperature gradient (Marangoni effect shifts the angle)
    """
    ca_left = params.get("left_contact_angle", 25.0)
    ca_right = params.get("right_contact_angle", 15.0)
    sigma = params.get("surface_tension", 0.35)
    mu = params.get("droplet_viscosity", 0.002)

    t_left = params.get("left_substrate_temperature", 303.15)
    t_right = params.get("right_substrate_temperature", 383.15)
    delta_t = t_right - t_left

    marangoni_shift = 0.02 * delta_t * (sigma / 0.35)
    viscosity_correction = 5.0 * (mu - 0.002)

    effective_left = ca_left + marangoni_shift * 0.3 + viscosity_correction
    effective_right = ca_right - marangoni_shift * 0.2 + viscosity_correction * 0.5

    effective_left = max(1.0, min(179.0, effective_left))
    effective_right = max(1.0, min(179.0, effective_right))

    return effective_left, effective_right


def generate_mock_comsol_output(params: Dict[str, float],
                                output_path: str,
                                material_names: Optional[Dict[str, str]] = None,
                                n_points: int = 3000) -> str:
    """
    Generate a mock COMSOL output TXT file.

    The file has the same format as real COMSOL exports:
    - Header line: x  y  z  IsoLevel
    - Data lines:  float  float  float  0.5

    Returns the path to the generated file and the effective contact angles.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    eff_left, eff_right = compute_effective_contact_angle(params)
    avg_angle = (eff_left + eff_right) / 2.0

    points = _spherical_cap_points(avg_angle, radius=2.0, n_points=n_points)

    with open(output_path, "w") as f:
        f.write(" x                       y                        z                        IsoLevel\n")
        for p in points:
            f.write(f" {p[0]:<24.16f} {p[1]:<24.16f} {p[2]:<24.16f} 0.5\n")

    return output_path


def run_mock_simulation(params: Dict[str, float],
                        work_dir: str,
                        material_names: Optional[Dict[str, str]] = None,
                        run_id: int = 0) -> str:
    """
    Mock replacement for run_comsol_simulation.

    Returns the path to the generated output TXT file.
    """
    os.makedirs(work_dir, exist_ok=True)
    txt_dir = os.path.join(work_dir, "txtresult")
    os.makedirs(txt_dir, exist_ok=True)

    output_path = os.path.join(txt_dir, f"simulation_result{run_id}.txt")
    generate_mock_comsol_output(params, output_path, material_names)

    return output_path
