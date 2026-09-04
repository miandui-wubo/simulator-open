#!/usr/bin/env bash
set -euo pipefail

# Ensure script runs from repository root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Try to switch Windows console code page to UTF-8 when available.
if command -v cmd.exe >/dev/null 2>&1; then
  # Use //c to avoid MSYS path conversion turning /c into C:/.
  cmd.exe //c chcp 65001 > /dev/null || true
elif command -v chcp.com >/dev/null 2>&1; then
  chcp.com 65001 > /dev/null || true
fi

# Force Python stdio/process encoding to UTF-8.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

# Optional overrides:
#   EXPERIMENTS_CSV=./input/experiments_preprocessed.csv
#   BATCH_OUTPUT=./simulation_workspace/batch_results_full
#   RUNTIME_DATASET_OUT=./input/experiments_runtime.jsonl
#   COMSOL_TIMEOUT_SECONDS=7200  (one MATLAB/COMSOL eval; raise if batch logs show batch_timeout at this cap)
#   TOLERANCE_DEG=1.0  (final contact-angle acceptance threshold in degrees)
EXPERIMENTS_CSV="${EXPERIMENTS_CSV:-./input/experiments_preprocessed.csv}"
BATCH_OUTPUT="${BATCH_OUTPUT:-./simulation_workspace/batch_results_full2}"
RUNTIME_DATASET_OUT="${RUNTIME_DATASET_OUT:-./input/experiments_runtime.jsonl}"
COMSOL_TIMEOUT_SECONDS="${COMSOL_TIMEOUT_SECONDS:-7200}"
TOLERANCE_DEG="${TOLERANCE_DEG:-1.0}"

# Enforce single-process execution across concurrent invocations.
LOCK_DIR="${LOCK_DIR:-./simulation_workspace/.run_batch_utf8.lock}"
LOCK_WAIT_SECONDS="${LOCK_WAIT_SECONDS:-0}"
start_ts="$(date +%s)"

acquire_lock() {
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    if [[ "$LOCK_WAIT_SECONDS" -eq 0 ]]; then
      echo "[run_batch_utf8] Another run is active: $LOCK_DIR"
      echo "[run_batch_utf8] Exit to keep single-process execution."
      exit 1
    fi

    now_ts="$(date +%s)"
    elapsed="$((now_ts - start_ts))"
    if (( elapsed >= LOCK_WAIT_SECONDS )); then
      echo "[run_batch_utf8] Timed out waiting for lock: $LOCK_DIR"
      exit 1
    fi
    sleep 2
  done
}

release_lock() {
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}

acquire_lock
trap release_lock EXIT INT TERM

python -u -m simulator.main \
  --experiments-csv "$EXPERIMENTS_CSV" \
  --batch-output "$BATCH_OUTPUT" \
  --runtime-dataset-out "$RUNTIME_DATASET_OUT" \
  --comsol-timeout "$COMSOL_TIMEOUT_SECONDS" \
  --tolerance "$TOLERANCE_DEG" \
  "$@"
