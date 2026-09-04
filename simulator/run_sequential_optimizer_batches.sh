#!/usr/bin/env bash
set -euo pipefail

# Run optimizer batches sequentially (one phase at a time):
#   1) Bayesian retry for 19 non-converged experiments
#   2) GA full batch (32 experiments)
#
# Usage:
#   bash simulator/run_sequential_optimizer_batches.sh
#
# Optional env overrides:
#   ITERATIONS=60          # applies to all phases unless phase script overrides
#   TOLERANCE_DEG=1.0
#   COMSOL_TIMEOUT_SECONDS=7200

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

export TOLERANCE_DEG="${TOLERANCE_DEG:-1.0}"
export COMSOL_TIMEOUT_SECONDS="${COMSOL_TIMEOUT_SECONDS:-7200}"
export LOCK_DIR="${LOCK_DIR:-./simulation_workspace/.run_batch_utf8.lock}"

LOG_DIR="./simulation_workspace/logs"
mkdir -p "$LOG_DIR"
MASTER_LOG="$LOG_DIR/sequential_optimizer_batches_$(date +%Y%m%d_%H%M%S).log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$MASTER_LOG"
}

run_phase() {
  local name="$1"
  shift
  log "========== START: $name =========="
  if "$@" >>"$MASTER_LOG" 2>&1; then
    log "========== DONE:  $name =========="
    return 0
  fi
  local code=$?
  log "========== FAIL:  $name (exit=$code) =========="
  return "$code"
}

log "Sequential optimizer batches starting"
log "Repo: $(pwd)"
log "Master log: $MASTER_LOG"

run_phase "Bayesian retry (19 non-converged)" \
  bash "$SCRIPT_DIR/run_batch_bayesian_retry.sh"

run_phase "GA full (32 experiments)" \
  bash "$SCRIPT_DIR/run_batch_ga_full.sh"

log "All sequential optimizer batches completed successfully."
