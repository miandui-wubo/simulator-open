#!/usr/bin/env python3
"""
Entry point for the integrated simulator pipeline.

Usage:
    python -m simulator.main                   # Run with defaults (mock COMSOL)
    python -m simulator.main --optimizer pso   # Use PSO optimizer
    python -m simulator.main --iterations 30   # Custom iteration count
"""

import argparse
import sys
import os
import io
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simulator.batch_runner import run_batch
from simulator.config import LLMCodegenConfig, MaterialConfig, SimulationConfig
from simulator.llm_codegen import healthcheck_local_codegen
from simulator.pipeline import run_pipeline


def _configure_utf8_stdio() -> None:
    """Force UTF-8 stdio to avoid Windows GBK encode/decode issues."""
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class _TeeStream(io.TextIOBase):
    """Mirror writes to console and a log file."""

    def __init__(self, original_stream, file_stream):
        self._original_stream = original_stream
        self._file_stream = file_stream

    def write(self, s):
        written = self._original_stream.write(s)
        try:
            self._file_stream.write(s)
        except ValueError:
            # File may already be closed during interpreter shutdown.
            pass
        return written

    def flush(self):
        self._original_stream.flush()
        try:
            self._file_stream.flush()
        except ValueError:
            # File may already be closed during interpreter shutdown.
            pass

    @property
    def encoding(self):
        return getattr(self._original_stream, "encoding", "utf-8")


def _resolve_log_dir(args) -> str:
    if args.log_dir:
        return os.path.abspath(args.log_dir)
    base = args.batch_output if args.experiments_csv else args.work_dir
    return os.path.join(os.path.abspath(base), "logs")


def _setup_auto_log(args):
    log_dir = _resolve_log_dir(args)
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "batch" if args.experiments_csv else "single"
    log_path = os.path.join(log_dir, f"{mode}_{timestamp}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = _TeeStream(sys.stdout, log_file)
    sys.stderr = _TeeStream(sys.stderr, log_file)
    print(f"[Log] Auto log enabled: {log_path}")
    return log_path, log_file


def main():
    _configure_utf8_stdio()
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    parser = argparse.ArgumentParser(
        description="Simulator: liquid metal alloy contact angle parameter search"
    )
    parser.add_argument(
        "--optimizer", choices=["bayesian", "pso", "ga"], default="pso",
        help="Optimization algorithm (default: pso)"
    )
    parser.add_argument(
        "--iterations", type=int, default=30,
        help="Maximum optimization iterations (default: 30)"
    )
    parser.add_argument(
        "--tolerance", type=float, default=1.0,
        help="Acceptable contact angle error in degrees (default: 1.0)"
    )
    parser.add_argument(
        "--target-left", type=float, default=27.27,
        help="Target left substrate contact angle (degrees)"
    )
    parser.add_argument(
        "--target-right", type=float, default=13.43,
        help="Target right substrate contact angle (degrees)"
    )
    parser.add_argument(
        "--droplet", type=str, default="Ga",
        help="Droplet material name"
    )
    parser.add_argument(
        "--left-substrate", type=str, default="Si",
        help="Left substrate material name"
    )
    parser.add_argument(
        "--right-substrate", type=str, default="GaN",
        help="Right substrate material name"
    )
    parser.add_argument(
        "--use-mock", action="store_true", default=False,
        help="Use mock COMSOL simulator (default: False, use real COMSOL if available)"
    )
    parser.add_argument(
        "--comsol-bin", type=str,
        default=r"C:\Program Files\COMSOL\COMSOL61\Multiphysics\bin\win64",
        help="COMSOL bin directory path"
    )
    parser.add_argument(
        "--comsol-mli", type=str,
        default=r"C:\Program Files\COMSOL\COMSOL61\Multiphysics\mli",
        help="COMSOL MLI directory path"
    )
    parser.add_argument(
        "--comsol-timeout", type=int, default=7200,
        help="MATLAB/COMSOL single-run timeout in seconds (default: 7200)"
    )
    parser.add_argument(
        "--max-consecutive-failures", type=int, default=20,
        help="Abort an experiment after N consecutive failed COMSOL evaluations before any success (default: 20)"
    )
    parser.add_argument(
        "--work-dir", type=str, default="./simulation_workspace",
        help="Working directory for simulation files"
    )
    parser.add_argument(
        "--experiments-csv", type=str, default=None,
        help="Batch mode: path to experiments_preprocessed.csv"
    )
    parser.add_argument(
        "--runtime-dataset-out", type=str, default="./input/experiments_runtime.jsonl",
        help="Path for normalized runtime dataset JSONL"
    )
    parser.add_argument(
        "--batch-output", type=str, default="./simulation_workspace/batch_results",
        help="Directory for batch results"
    )
    parser.add_argument(
        "--batch-limit", type=int, default=0,
        help="Run only first N experiments in batch mode (0 means all)"
    )
    parser.add_argument(
        "--resume-batch", action=argparse.BooleanOptionalAction, default=True,
        help="Resume batch runs from existing batch_results.jsonl/csv in --batch-output (default: True)"
    )
    parser.add_argument(
        "--log-dir", type=str, default=None,
        help="Directory for auto-saved run logs (default: <work-dir>/logs or <batch-output>/logs)"
    )
    parser.add_argument(
        "--llm-once", action=argparse.BooleanOptionalAction, default=True,
        help="Call local LLM once to generate parameter template, then reuse cache"
    )
    parser.add_argument(
        "--llm-model-dir", type=str, default="./comsol_work/model/matlab_checkpoint-39",
        help="Local checkpoint directory for one-time LLM template generation"
    )
    parser.add_argument(
        "--llm-prompt-path", type=str, default="./simulator/prompt/matlab_param_template_prompt.md",
        help="Prompt file for generating MATLAB parameter template"
    )
    parser.add_argument(
        "--llm-cache-path", type=str, default="./simulation_workspace/llm_cache/param_code_template.m",
        help="Cache file path for one-time generated MATLAB parameter template"
    )
    parser.add_argument(
        "--llm-timeout", type=int, default=600,
        help="Timeout (seconds) for local LLM inference call"
    )
    parser.add_argument(
        "--allow-fallback-template", action="store_true", default=False,
        help="Fallback to deterministic template when local LLM generation fails"
    )
    parser.add_argument(
        "--check-llm-model", action="store_true", default=False,
        help="Run local LLM model health check and exit"
    )

    args = parser.parse_args()

    log_file = None
    exit_code = 1
    try:
        _, log_file = _setup_auto_log(args)

        if args.check_llm_model:
            check = healthcheck_local_codegen(
                model_dir=args.llm_model_dir,
                prompt_path=args.llm_prompt_path,
                timeout_seconds=args.llm_timeout,
            )
            print(f"[LLM Healthcheck] ok={check.get('ok')} reason={check.get('reason')}")
            exit_code = 0 if check.get("ok") else 1
            return exit_code

        if args.experiments_csv:
            exit_code = run_batch(args)
            return exit_code

        config = SimulationConfig(
            target_left_contact_angle=args.target_left,
            target_right_contact_angle=args.target_right,
            material=MaterialConfig(
                droplet_name=args.droplet,
                left_substrate_name=args.left_substrate,
                right_substrate_name=args.right_substrate,
            ),
            tolerance_deg=args.tolerance,
            max_iterations=args.iterations,
            optimizer=args.optimizer,
            use_mock=args.use_mock,
            work_dir=args.work_dir,
            comsol_bin_dir=args.comsol_bin,
            comsol_mli_dir=args.comsol_mli,
            comsol_timeout_seconds=args.comsol_timeout,
            max_consecutive_failures=args.max_consecutive_failures,
            llm_codegen=LLMCodegenConfig(
                enabled=args.llm_once,
                model_dir=args.llm_model_dir,
                prompt_path=args.llm_prompt_path,
                cache_path=args.llm_cache_path,
                allow_fallback_template=args.allow_fallback_template,
                timeout_seconds=args.llm_timeout,
            ),
        )

        result = run_pipeline(config)
        exit_code = 0 if result["converged"] else 1
        return exit_code
    finally:
        if log_file is not None:
            completion_line = f"[Log] Run completed with exit_code={exit_code}"
            try:
                original_stdout.write(completion_line + "\n")
                original_stdout.flush()
            except Exception:
                pass
            try:
                log_file.write(completion_line + "\n")
                log_file.flush()
            except Exception:
                pass
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            log_file.close()


if __name__ == "__main__":
    sys.exit(main())
