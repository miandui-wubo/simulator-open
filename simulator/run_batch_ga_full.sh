#!/usr/bin/env bash
set -euo pipefail

# Full batch (32 experiments) with Genetic Algorithm (DEAP).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export EXPERIMENTS_CSV="${EXPERIMENTS_CSV:-./input/experiments_preprocessed.csv}"
export BATCH_OUTPUT="${BATCH_OUTPUT:-./simulation_workspace/batch_results_ga}"
export RUNTIME_DATASET_OUT="${RUNTIME_DATASET_OUT:-./input/experiments_ga_runtime.jsonl}"
export LOCK_DIR="${LOCK_DIR:-./simulation_workspace/.run_batch_utf8.lock}"

exec bash "$SCRIPT_DIR/run_batch_utf8.sh" \
  --optimizer ga \
  --iterations "${ITERATIONS:-30}" \
  "$@"
