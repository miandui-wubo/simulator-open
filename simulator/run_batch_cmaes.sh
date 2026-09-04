#!/usr/bin/env bash
set -euo pipefail

# Batch run with CMA-ES (Covariance Matrix Adaptation Evolution Strategy).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export BATCH_OUTPUT="${BATCH_OUTPUT:-./simulation_workspace/batch_results_cmaes}"
export LOCK_DIR="${LOCK_DIR:-./simulation_workspace/.run_batch_utf8.lock}"

exec bash "$SCRIPT_DIR/run_batch_utf8.sh" --optimizer cmaes "$@"
