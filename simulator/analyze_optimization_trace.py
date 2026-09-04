#!/usr/bin/env python3
"""
Analyze optimization traces and generate sensitivity/importance reports.

Usage example:
    python -m simulator.analyze_optimization_trace \
      --trace-csv ./simulation_workspace/optimization_trace/optimization_trace.csv \
      --output-dir ./simulation_workspace/optimization_trace/analysis
"""

from __future__ import annotations

import argparse
import os
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance


META_COLUMNS = {
    "iteration",
    "run_id",
    "status",
    "error",
    "simulated_contact_angle",
    "target_contact_angle_avg",
    "txt_path",
    "failure_reason",
}


def _resolve_trace_csv(args) -> str:
    if args.trace_csv:
        return os.path.abspath(args.trace_csv)
    return os.path.abspath(
        os.path.join(args.work_dir, "optimization_trace", "optimization_trace.csv")
    )


def _load_trace(trace_csv: str) -> pd.DataFrame:
    if not os.path.exists(trace_csv):
        raise FileNotFoundError(f"Trace CSV not found: {trace_csv}")
    df = pd.read_csv(trace_csv)
    if "error" not in df.columns:
        raise ValueError("Trace CSV must include an 'error' column.")
    return df


def _get_feature_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c not in META_COLUMNS]


def _prepare_training_data(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, pd.Series]:
    filtered = df.copy()
    if "status" in filtered.columns:
        filtered = filtered[filtered["status"] == "success"]
    filtered = filtered.dropna(subset=feature_cols + ["error"])
    if filtered.empty:
        raise ValueError("No valid successful evaluations found for analysis.")
    x = filtered[feature_cols]
    y = filtered["error"]
    return x, y


def _fit_surrogate(x: pd.DataFrame, y: pd.Series, random_state: int = 42) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=400,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    model.fit(x, y)
    return model


def _save_global_importance(
    model: RandomForestRegressor,
    x: pd.DataFrame,
    y: pd.Series,
    output_dir: str,
) -> pd.DataFrame:
    result = permutation_importance(
        model,
        x,
        y,
        n_repeats=30,
        random_state=42,
        n_jobs=-1,
    )
    importance_df = pd.DataFrame(
        {
            "parameter": x.columns,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)

    csv_path = os.path.join(output_dir, "global_importance_ranking.csv")
    importance_df.to_csv(csv_path, index=False, encoding="utf-8")

    plt.figure(figsize=(10, max(4, 0.4 * len(importance_df))))
    plt.barh(
        importance_df["parameter"][::-1],
        importance_df["importance_mean"][::-1],
        xerr=importance_df["importance_std"][::-1],
    )
    plt.xlabel("Permutation Importance")
    plt.title("Global Parameter Importance Ranking")
    plt.tight_layout()
    fig_path = os.path.join(output_dir, "global_importance_ranking.png")
    plt.savefig(fig_path, dpi=180)
    plt.close()

    print(f"[Analysis] Global importance CSV: {csv_path}")
    print(f"[Analysis] Global importance figure: {fig_path}")
    return importance_df


def _save_local_sensitivity_curves(
    model: RandomForestRegressor,
    x: pd.DataFrame,
    y: pd.Series,
    output_dir: str,
    n_grid: int = 80,
) -> None:
    best_idx = int(np.argmin(y.values))
    reference_row = x.iloc[best_idx].copy()

    n_features = len(x.columns)
    n_cols = 3
    n_rows = int(np.ceil(n_features / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 3.4 * n_rows))
    axes = np.atleast_1d(axes).flatten()

    curve_records = []
    for i, col in enumerate(x.columns):
        col_min = float(x[col].min())
        col_max = float(x[col].max())
        grid = np.linspace(col_min, col_max, n_grid)

        sweep = pd.DataFrame([reference_row.values] * n_grid, columns=x.columns)
        sweep[col] = grid
        pred = model.predict(sweep)

        ax = axes[i]
        ax.plot(grid, pred, linewidth=2)
        ax.axvline(float(reference_row[col]), linestyle="--", linewidth=1)
        ax.set_title(col)
        ax.set_xlabel(col)
        ax.set_ylabel("Predicted error")
        ax.grid(alpha=0.3)

        for g, p in zip(grid, pred):
            curve_records.append(
                {
                    "parameter": col,
                    "parameter_value": float(g),
                    "predicted_error": float(p),
                    "reference_value": float(reference_row[col]),
                }
            )

    for j in range(n_features, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Local Sensitivity Curves (one-parameter sweep around best point)")
    plt.tight_layout()
    fig_path = os.path.join(output_dir, "local_sensitivity_curves.png")
    plt.savefig(fig_path, dpi=180)
    plt.close(fig)

    curves_path = os.path.join(output_dir, "local_sensitivity_curves.csv")
    pd.DataFrame(curve_records).to_csv(curves_path, index=False, encoding="utf-8")
    print(f"[Analysis] Local sensitivity figure: {fig_path}")
    print(f"[Analysis] Local sensitivity CSV: {curves_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze optimization traces: local sensitivity + global importance"
    )
    parser.add_argument(
        "--trace-csv",
        type=str,
        default=None,
        help="Path to optimization_trace.csv. If omitted, infer from --work-dir.",
    )
    parser.add_argument(
        "--work-dir",
        type=str,
        default="./simulation_workspace",
        help="Work directory used by simulator pipeline.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save analysis results. Default: <trace-dir>/analysis",
    )
    args = parser.parse_args()

    trace_csv = _resolve_trace_csv(args)
    trace_dir = os.path.dirname(trace_csv)
    output_dir = (
        os.path.abspath(args.output_dir)
        if args.output_dir
        else os.path.join(trace_dir, "analysis")
    )
    os.makedirs(output_dir, exist_ok=True)

    df = _load_trace(trace_csv)
    feature_cols = _get_feature_columns(df)
    x, y = _prepare_training_data(df, feature_cols)
    model = _fit_surrogate(x, y)
    _save_global_importance(model, x, y, output_dir)
    _save_local_sensitivity_curves(model, x, y, output_dir)

    print(f"[Analysis] Completed. Outputs in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
