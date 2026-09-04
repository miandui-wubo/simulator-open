"""
Main optimization pipeline.

Connects parameter-search → comsol_work → contact-angle in a closed loop.
"""

import os
import sys
import time
import csv
import json
import numpy as np
from typing import Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'parameter-search'))

from src.core.parameter_space import Parameter, ParameterSpace
from src.core.objective import BaseObjective, OptimizationConverged
from src.optimizers.bayesian_optimizer import BayesianOptimizer
from src.optimizers.genetic_algorithm import GeneticAlgorithm
from src.optimizers.pso_optimizer import ParticleSwarmOptimizer
from src.optimizers.cmaes_optimizer import CMAESOptimizer

from simulator.config import SimulationConfig
from simulator.contact_angle_interface import compute_contact_angle
from simulator.mock_comsol import run_mock_simulation


def _safe_console_text(text: str) -> str:
    """Best-effort conversion to avoid console encoding crashes on Windows."""
    if not text:
        return text
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


class ContactAngleObjective(BaseObjective):
    """
    Objective function that runs a COMSOL simulation (or mock) and compares
    the resulting contact angle with the experimental target.

    Error = |simulated_left_angle - target_left| + |simulated_right_angle - target_right|
    """

    def __init__(self, config: SimulationConfig, param_space: ParameterSpace):
        super().__init__()
        self.config = config
        self.param_space = param_space
        self._run_counter = 0
        self._successful_runs = 0
        self._consecutive_failures = 0
        self.run_records = []
        self.stop_requested = False
        self.stop_reason = ""

    def evaluate(self, params: np.ndarray) -> float:
        params_dict = self.param_space.array_to_dict(params)

        material_names = {
            "droplet_name": self.config.material.droplet_name,
            "left_substrate_name": self.config.material.left_substrate_name,
            "right_substrate_name": self.config.material.right_substrate_name,
        }

        run_id = self._run_counter
        self._run_counter += 1

        try:
            if self.config.use_mock:
                txt_path = run_mock_simulation(
                    params_dict, self.config.work_dir, material_names, run_id
                )
            else:
                from simulator.comsol_interface import run_comsol_simulation
                txt_path = run_comsol_simulation(
                    params_dict,
                    os.path.join(self.config.work_dir, "matlabcode"),
                    self.config.comsol_bin_dir,
                    self.config.comsol_mli_dir,
                    material_names,
                    self.config.llm_codegen,
                    run_id,
                    self.config.comsol_timeout_seconds,
                )

            simulated_angle = compute_contact_angle(txt_path)

            target_avg = (self.config.target_left_contact_angle +
                          self.config.target_right_contact_angle) / 2.0
            error = abs(simulated_angle - target_avg)
            self.run_records.append(
                {
                    "run_id": run_id,
                    "status": "success",
                    "txt_path": txt_path,
                    "simulated_contact_angle": float(simulated_angle),
                    "target_contact_angle_avg": float(target_avg),
                    "error": float(error),
                    "params": dict(params_dict),
                }
            )
            self._successful_runs += 1
            self._consecutive_failures = 0
            self.stop_requested = error <= self.config.tolerance_deg
            if self.stop_requested:
                self.stop_reason = (
                    f"Converged at run {run_id}: error={error:.4f}° "
                    f"<= tolerance={self.config.tolerance_deg:.4f}°"
                )

            return error

        except Exception as e:
            import traceback
            print(_safe_console_text(f"[Iteration {run_id}] Simulation failed: {e}"))
            print(_safe_console_text(f"[Iteration {run_id}] Traceback: {traceback.format_exc()}"))
            target_avg = (self.config.target_left_contact_angle +
                          self.config.target_right_contact_angle) / 2.0
            self.run_records.append(
                {
                    "run_id": run_id,
                    "status": "failed",
                    "txt_path": "",
                    "simulated_contact_angle": None,
                    "target_contact_angle_avg": float(target_avg),
                    "error": float(1e6),
                    "params": dict(params_dict),
                    "failure_reason": str(e),
                }
            )
            self._consecutive_failures += 1
            max_failures = int(getattr(self.config, "max_consecutive_failures", 0) or 0)
            if (
                max_failures > 0
                and self._successful_runs == 0
                and self._consecutive_failures >= max_failures
            ):
                raise RuntimeError(
                    "Aborting experiment after "
                    f"{self._consecutive_failures} consecutive failed COMSOL evaluations "
                    "before any successful output TXT was produced."
                ) from e
            return 1e6


def build_parameter_space(config: SimulationConfig) -> ParameterSpace:
    """Build a ParameterSpace from config search bounds."""
    params = []
    for name, (lo, hi) in config.search_bounds.items():
        params.append(Parameter(name=name, lower_bound=lo, upper_bound=hi))
    return ParameterSpace(params)


def _parse_float_or_none(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _prepare_ga_warm_start(
    config: SimulationConfig,
    param_space: ParameterSpace,
    objective: "ContactAngleObjective",
):
    """Continue a non-converged GA run from its prior optimization trace.

    Prior successful evaluations are registered on the objective so the newly
    saved trace extends the old one and best-so-far is preserved, and the best
    points seed the initial GA population with their known fitness (no COMSOL
    re-evaluation). Enabled per experiment via the environment variable
    SIMULATOR_WARM_START_EXPERIMENTS, e.g. "exp_014,exp_017".

    Returns (seed_points, already_converged).
    """
    seed_points = []
    warm_ids = [
        s.strip()
        for s in os.environ.get("SIMULATOR_WARM_START_EXPERIMENTS", "").split(",")
        if s.strip()
    ]
    exp_id = os.path.basename(os.path.abspath(config.work_dir))
    if config.optimizer != "ga" or exp_id not in warm_ids:
        return seed_points, False

    trace_csv = os.path.join(
        os.path.abspath(config.work_dir), "optimization_trace", "optimization_trace.csv"
    )
    if not os.path.exists(trace_csv):
        print(f"[WarmStart] No prior trace for {exp_id}; starting fresh")
        return seed_points, False

    param_names = param_space.get_param_names()
    parsed = []
    seen = set()
    with open(trace_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if str(row.get("status", "")).lower() != "success":
                continue
            try:
                params_dict = {name: float(row[name]) for name in param_names}
                error = float(row["error"])
            except (KeyError, TypeError, ValueError):
                continue
            key = tuple(round(params_dict[name], 9) for name in param_names)
            if key in seen:
                continue
            seen.add(key)
            parsed.append((params_dict, error, row))
    if not parsed:
        print(f"[WarmStart] Prior trace for {exp_id} has no usable rows; starting fresh")
        return seed_points, False

    parsed.sort(key=lambda item: item[1])

    # Register prior evaluations so the saved trace and the reported best
    # continue from the previous run instead of restarting at iteration 1.
    for idx, (params_dict, error, row) in enumerate(parsed, start=1):
        objective.n_evaluations = idx
        objective.evaluation_history.append(
            {
                "params": param_space.dict_to_array(params_dict),
                "value": error,
                "time": 0.0,
                "iteration": idx,
            }
        )
        objective.run_records.append(
            {
                "run_id": int(row.get("run_id", -1) or -1),
                "status": "warm_start",
                "txt_path": row.get("txt_path", ""),
                "simulated_contact_angle": _parse_float_or_none(
                    row.get("simulated_contact_angle")
                ),
                "target_contact_angle_avg": _parse_float_or_none(
                    row.get("target_contact_angle_avg")
                ),
                "error": error,
                "params": params_dict,
            }
        )
    objective.best_value = parsed[0][1]
    objective.best_params = param_space.dict_to_array(parsed[0][0])

    # Match the GA population size used in run_pipeline.
    seed_points = [
        (param_space.clip(param_space.dict_to_array(pd)), err)
        for pd, err, _ in parsed[:20]
    ]
    print(
        f"[WarmStart] {exp_id}: continuing from {len(parsed)} prior evaluations "
        f"(best error={objective.best_value:.4f}°), "
        f"seeding {len(seed_points)} individuals with known fitness"
    )
    if objective.best_value <= config.tolerance_deg:
        print("[WarmStart] Prior trace already within tolerance; skip new evaluations")
        return seed_points, True
    return seed_points, False


def _save_optimization_trace(config: SimulationConfig, objective: ContactAngleObjective, param_space: ParameterSpace) -> Dict[str, str]:
    """Save per-evaluation optimization trace to CSV/JSONL."""
    trace_dir = os.path.join(os.path.abspath(config.work_dir), "optimization_trace")
    os.makedirs(trace_dir, exist_ok=True)
    csv_path = os.path.join(trace_dir, "optimization_trace.csv")
    jsonl_path = os.path.join(trace_dir, "optimization_trace.jsonl")
    param_names = param_space.get_param_names()

    columns = [
        "iteration",
        "run_id",
        "status",
        "error",
        "simulated_contact_angle",
        "target_contact_angle_avg",
        "txt_path",
        "failure_reason",
    ] + param_names

    with open(csv_path, "w", encoding="utf-8", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=columns)
        writer.writeheader()
        for eval_item, run_item in zip(objective.evaluation_history, objective.run_records):
            row = {
                "iteration": int(eval_item.get("iteration", 0)),
                "run_id": int(run_item.get("run_id", -1)),
                "status": run_item.get("status", "unknown"),
                "error": float(eval_item.get("value", run_item.get("error", 1e6))),
                "simulated_contact_angle": run_item.get("simulated_contact_angle"),
                "target_contact_angle_avg": run_item.get("target_contact_angle_avg"),
                "txt_path": run_item.get("txt_path", ""),
                "failure_reason": run_item.get("failure_reason", ""),
            }
            for name in param_names:
                row[name] = float(run_item.get("params", {}).get(name))
            writer.writerow(row)

    with open(jsonl_path, "w", encoding="utf-8") as f_jsonl:
        for eval_item, run_item in zip(objective.evaluation_history, objective.run_records):
            record = {
                "iteration": int(eval_item.get("iteration", 0)),
                "run_id": int(run_item.get("run_id", -1)),
                "status": run_item.get("status", "unknown"),
                "error": float(eval_item.get("value", run_item.get("error", 1e6))),
                "simulated_contact_angle": run_item.get("simulated_contact_angle"),
                "target_contact_angle_avg": run_item.get("target_contact_angle_avg"),
                "txt_path": run_item.get("txt_path", ""),
                "failure_reason": run_item.get("failure_reason", ""),
                "params": run_item.get("params", {}),
            }
            f_jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[Trace] Saved optimization trace CSV: {csv_path}")
    print(f"[Trace] Saved optimization trace JSONL: {jsonl_path}")
    return {"csv": csv_path, "jsonl": jsonl_path}


def run_pipeline(config: SimulationConfig) -> Dict:
    """
    Run the full optimization pipeline.

    Returns a dict with:
      - best_params: optimal parameter dict
      - best_error: smallest contact angle error (degrees)
      - converged: whether error < tolerance
      - history: list of (iteration, error) tuples
    """
    print("=" * 70)
    print("Simulator Pipeline - Contact Angle Parameter Search")
    print("=" * 70)
    print(f"Target left contact angle:  {config.target_left_contact_angle}°")
    print(f"Target right contact angle: {config.target_right_contact_angle}°")
    print(f"Tolerance: {config.tolerance_deg}°")
    print(f"Optimizer: {config.optimizer}")
    print(f"Max iterations: {config.max_iterations}")
    print(f"Mode: {'Mock COMSOL' if config.use_mock else 'Real COMSOL'}")
    print(f"Parameters to search: {list(config.search_bounds.keys())}")
    print("=" * 70)

    param_space = build_parameter_space(config)
    objective = ContactAngleObjective(config, param_space)

    start_time = time.time()

    if config.optimizer == "bayesian":
        optimizer = BayesianOptimizer(
            param_space=param_space,
            objective=objective,
            n_initial_points=min(10, config.max_iterations // 3),
        )
        try:
            best_params = optimizer.optimize(
                n_iterations=config.max_iterations, verbose=True
            )
        except OptimizationConverged as exc:
            print(f"[Early Stop] {exc}")
            best_params = objective.best_params
    elif config.optimizer == "pso":
        optimizer = ParticleSwarmOptimizer(
            param_space=param_space,
            objective=objective,
            n_particles=20,
        )
        try:
            best_params = optimizer.optimize(
                n_iterations=config.max_iterations, verbose=True
            )
        except OptimizationConverged as exc:
            print(f"[Early Stop] {exc}")
            best_params = objective.best_params
    elif config.optimizer == "ga":
        seed_points, warm_already_converged = _prepare_ga_warm_start(
            config, param_space, objective
        )
        if warm_already_converged:
            best_params = objective.best_params
        else:
            optimizer = GeneticAlgorithm(
                param_space=param_space,
                objective=objective,
                population_size=20,
                seed_points=seed_points,
            )
            try:
                best_params = optimizer.optimize(
                    n_generations=config.max_iterations, verbose=True
                )
            except OptimizationConverged as exc:
                print(f"[Early Stop] {exc}")
                best_params = objective.best_params
    elif config.optimizer == "cmaes":
        optimizer = CMAESOptimizer(
            param_space=param_space,
            objective=objective,
        )
        try:
            best_params = optimizer.optimize(
                n_iterations=config.max_iterations, verbose=True
            )
        except OptimizationConverged as exc:
            print(f"[Early Stop] {exc}")
            best_params = objective.best_params
    else:
        raise ValueError(f"Unknown optimizer: {config.optimizer}")

    elapsed = time.time() - start_time

    best_dict = param_space.array_to_dict(best_params)
    best_error = objective.best_value
    converged = best_error <= config.tolerance_deg

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Converged: {converged}")
    print(f"Best error: {best_error:.4f}°")
    print(f"Evaluations: {objective.n_evaluations}")
    print(f"Time: {elapsed:.1f}s")
    print("\nBest parameters:")
    for name, value in best_dict.items():
        print(f"  {name}: {value:.6f}")

    if converged:
        print(f"\nFound parameters within {config.tolerance_deg}° tolerance.")
    else:
        print(f"\nDid not converge within {config.tolerance_deg}° tolerance.")
        print(f"    Best error was {best_error:.4f}°")

    print("=" * 70)

    history = [
        (h["iteration"], h["value"])
        for h in objective.evaluation_history
    ]
    trace_paths = _save_optimization_trace(config, objective, param_space)

    return {
        "best_params": best_dict,
        "best_error": best_error,
        "converged": converged,
        "history": history,
        "trace_paths": trace_paths,
        "elapsed_seconds": elapsed,
        "n_evaluations": objective.n_evaluations,
    }
