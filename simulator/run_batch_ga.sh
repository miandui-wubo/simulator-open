#!/usr/bin/env bash
set -euo pipefail

# Batch run with Genetic Algorithm (DEAP).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export BATCH_OUTPUT="${BATCH_OUTPUT:-./simulation_workspace/batch_results_ga}"
export LOCK_DIR="${LOCK_DIR:-./simulation_workspace/.run_batch_utf8.lock}"

exec bash "$SCRIPT_DIR/run_batch_utf8.sh" --optimizer ga "$@"
