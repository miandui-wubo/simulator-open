"""
Batch runner for multi-experiment simulation.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Dict, List

from simulator.config import LLMCodegenConfig, MaterialConfig, SimulationConfig
from simulator.experiment_dataset import load_experiments_csv, write_runtime_jsonl
from simulator.pipeline import run_pipeline


def _json_safe(value):
    """Convert numpy/scalar objects to JSON-serializable Python primitives."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _locked_range(value: float, eps: float = 1e-6) -> tuple:
    return (float(value - eps), float(value + eps))


def _build_config_from_experiment(
    exp: Dict,
    args,
    llm_cfg: LLMCodegenConfig,
) -> SimulationConfig:
    exp_id = exp["experiment_id"]
    exp_work_dir = os.path.join(os.path.abspath(args.work_dir), exp_id)
    search_bounds = dict(SimulationConfig().search_bounds)
    search_bounds["left_substrate_temperature"] = _locked_range(exp["left_substrate_temperature_k"])
    search_bounds["right_substrate_temperature"] = _locked_range(exp["right_substrate_temperature_k"])

    return SimulationConfig(
        target_left_contact_angle=exp["target_left_contact_angle"],
        target_right_contact_angle=exp["target_right_contact_angle"],
        material=MaterialConfig(
            droplet_name=exp["droplet_name"],
            left_substrate_name=exp["left_substrate_name"],
            right_substrate_name=exp["right_substrate_name"],
            mesh_fineness=exp["mesh_fineness"],
        ),
        search_bounds=search_bounds,
        tolerance_deg=args.tolerance,
        max_iterations=args.iterations,
        optimizer=args.optimizer,
        use_mock=args.use_mock,
        work_dir=exp_work_dir,
        comsol_bin_dir=args.comsol_bin,
        comsol_mli_dir=args.comsol_mli,
        comsol_timeout_seconds=args.comsol_timeout,
        max_consecutive_failures=args.max_consecutive_failures,
        llm_codegen=llm_cfg,
    )


def _write_batch_outputs(results: List[Dict], output_base: str) -> Dict[str, str]:
    output_base = os.path.abspath(output_base)
    os.makedirs(output_base, exist_ok=True)
    csv_path = os.path.join(output_base, "batch_results.csv")
    jsonl_path = os.path.join(output_base, "batch_results.jsonl")

    with open(jsonl_path, "w", encoding="utf-8") as f_jsonl:
        for row in results:
            safe_row = _json_safe(row)
            f_jsonl.write(json.dumps(safe_row, ensure_ascii=False) + "\n")

    csv_columns = [
        "experiment_id",
        "status",
        "converged",
        "best_error",
        "elapsed_seconds",
        "n_evaluations",
        "failure_reason",
        "best_params_json",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=csv_columns)
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "experiment_id": row.get("experiment_id"),
                    "status": row.get("status"),
                    "converged": row.get("converged"),
                    "best_error": row.get("best_error"),
                    "elapsed_seconds": row.get("elapsed_seconds"),
                    "n_evaluations": row.get("n_evaluations"),
                    "failure_reason": row.get("failure_reason", ""),
                    "best_params_json": json.dumps(
                        _json_safe(row.get("best_params", {})), ensure_ascii=False
                    ),
                }
            )

    return {"csv": csv_path, "jsonl": jsonl_path}


def _load_previous_results(output_base: str) -> List[Dict]:
    output_base = os.path.abspath(output_base)
    jsonl_path = os.path.join(output_base, "batch_results.jsonl")
    csv_path = os.path.join(output_base, "batch_results.csv")

    if os.path.exists(jsonl_path):
        rows: List[Dict] = []
        with open(jsonl_path, "r", encoding="utf-8") as f_jsonl:
            for line in f_jsonl:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        deduped: Dict[str, Dict] = {}
        ordered_ids: List[str] = []
        for row in rows:
            exp_id = row.get("experiment_id")
            if not exp_id:
                continue
            if exp_id not in deduped:
                ordered_ids.append(exp_id)
            deduped[exp_id] = row
        return [deduped[exp_id] for exp_id in ordered_ids]

    if os.path.exists(csv_path):
        rows = []
        with open(csv_path, "r", encoding="utf-8") as f_csv:
            reader = csv.DictReader(f_csv)
            for row in reader:
                best_params = row.get("best_params_json") or "{}"
                try:
                    parsed_best_params = json.loads(best_params)
                except json.JSONDecodeError:
                    parsed_best_params = {}
                rows.append(
                    {
                        "experiment_id": row.get("experiment_id"),
                        "status": row.get("status"),
                        "converged": str(row.get("converged")).lower() == "true",
                        "best_error": (
                            float(row["best_error"])
                            if row.get("best_error") not in (None, "", "None")
                            else None
                        ),
                        "elapsed_seconds": (
                            float(row["elapsed_seconds"])
                            if row.get("elapsed_seconds") not in (None, "", "None")
                            else None
                        ),
                        "n_evaluations": (
                            int(float(row["n_evaluations"]))
                            if row.get("n_evaluations") not in (None, "", "None")
                            else 0
                        ),
                        "best_params": parsed_best_params,
                        "failure_reason": row.get("failure_reason", ""),
                    }
                )
        deduped: Dict[str, Dict] = {}
        ordered_ids: List[str] = []
        for row in rows:
            exp_id = row.get("experiment_id")
            if not exp_id:
                continue
            if exp_id not in deduped:
                ordered_ids.append(exp_id)
            deduped[exp_id] = row
        return [deduped[exp_id] for exp_id in ordered_ids]

    return []


def _persist_batch_progress(results: List[Dict], output_base: str) -> Dict[str, str]:
    """Persist all known results so interrupted runs can resume."""
    return _write_batch_outputs(results, output_base)


def run_batch(args) -> int:
    experiments = load_experiments_csv(args.experiments_csv)
    if args.batch_limit and args.batch_limit > 0:
        experiments = experiments[:args.batch_limit]
        print(f"[Batch] Applying --batch-limit={args.batch_limit}")
    runtime_jsonl = os.path.abspath(args.runtime_dataset_out)
    write_runtime_jsonl(experiments, runtime_jsonl)
    print(f"[Batch] Normalized runtime dataset written to: {runtime_jsonl}")

    llm_cfg = LLMCodegenConfig(
        enabled=args.llm_once,
        model_dir=args.llm_model_dir,
        prompt_path=args.llm_prompt_path,
        cache_path=args.llm_cache_path,
        allow_fallback_template=args.allow_fallback_template,
        timeout_seconds=args.llm_timeout,
    )

    target_ids = {exp["experiment_id"] for exp in experiments}
    output_base = os.path.abspath(args.batch_output)
    previous_results: List[Dict] = []
    completed_ids = set()
    if args.resume_batch:
        previous_results = [
            row for row in _load_previous_results(output_base)
            if row.get("experiment_id") in target_ids
        ]
        completed_ids = {
            row.get("experiment_id")
            for row in previous_results
            if row.get("experiment_id")
        }
        if completed_ids:
            print(
                f"[Batch] Resume enabled: loaded {len(completed_ids)} completed records "
                f"from {output_base}"
            )

    results: List[Dict] = list(previous_results)
    for idx, exp in enumerate(experiments, start=1):
        exp_id = exp["experiment_id"]
        if exp_id in completed_ids:
            print(f"\n[Batch] Skipping completed experiment {idx}/{len(experiments)}: {exp_id}")
            continue

        print(f"\n[Batch] Running experiment {idx}/{len(experiments)}: {exp_id}")
        config = _build_config_from_experiment(exp, args, llm_cfg)

        try:
            run_result = run_pipeline(config)
            inferred_failure = run_result["best_error"] >= 9e5
            row = {
                "experiment_id": exp_id,
                "status": "failed" if inferred_failure else "success",
                "converged": run_result["converged"],
                "best_error": run_result["best_error"],
                "elapsed_seconds": run_result["elapsed_seconds"],
                "n_evaluations": run_result["n_evaluations"],
                "best_params": run_result["best_params"],
                "failure_reason": (
                    "All simulation evaluations failed (best_error indicates fallback penalty)."
                    if inferred_failure else ""
                ),
            }
        except Exception as exc:
            row = {
                "experiment_id": exp_id,
                "status": "failed",
                "converged": False,
                "best_error": None,
                "elapsed_seconds": None,
                "n_evaluations": 0,
                "best_params": {},
                "failure_reason": str(exc),
            }
            print(f"[Batch] Experiment failed: {exp_id} -> {exc}")
        results.append(row)
        _persist_batch_progress(results, output_base)
        completed_ids.add(exp_id)

    outputs = _write_batch_outputs(results, output_base)
    success_count = sum(1 for r in results if r["status"] == "success")
    print(
        f"[Batch] Completed {len(results)} experiments; success={success_count}, "
        f"failed={len(results) - success_count}"
    )
    print(f"[Batch] Result CSV: {outputs['csv']}")
    print(f"[Batch] Result JSONL: {outputs['jsonl']}")
    return 0 if success_count == len(results) else 1
