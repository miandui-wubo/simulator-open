#!/usr/bin/env bash
set -euo pipefail

# Retry Bayesian batch for 19 experiments that did not converge (fresh restart).
# Input:  input/experiments_bayesian_nonconverged.csv
# Output: simulation_workspace/batch_results_bayesian_retry/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export EXPERIMENTS_CSV="${EXPERIMENTS_CSV:-./input/experiments_bayesian_nonconverged.csv}"
export BATCH_OUTPUT="${BATCH_OUTPUT:-./simulation_workspace/batch_results_bayesian_retry}"
export RUNTIME_DATASET_OUT="${RUNTIME_DATASET_OUT:-./input/experiments_bayesian_nonconverged_runtime.jsonl}"
export LOCK_DIR="${LOCK_DIR:-./simulation_workspace/.run_batch_utf8.lock}"

exec bash "$SCRIPT_DIR/run_batch_utf8.sh" \
  --optimizer bayesian \
  --iterations "${ITERATIONS:-60}" \
  --no-resume-batch \
  "$@"
