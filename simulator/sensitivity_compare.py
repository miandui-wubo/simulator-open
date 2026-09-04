#!/usr/bin/env python3
"""
Bayesian vs PSO sensitivity analysis comparison.

Loads Bayesian traces and PSO batch results, then produces side-by-side:
  1. Global importance ranking (Bayesian vs PSO)
  2. Local sensitivity curves (Bayesian vs PSO)
  3. Aggregated importance ranking comparison

Usage:
    python -m simulator.sensitivity_compare
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRACE_GLOB = "exp_*/optimization_trace/optimization_trace.csv"

META_COLUMNS = {
    "iteration", "run_id", "status", "error",
    "simulated_contact_angle", "target_contact_angle_avg",
    "txt_path", "failure_reason",
}

LOCKED_PARAMETERS = {
    "left_substrate_temperature",
    "right_substrate_temperature",
}

PARAM_DISPLAY_NAMES = {
    "surface_tension": "Surface Tension [N/m]",
    "droplet_density": "Droplet Density [kg/m^3]",
    "droplet_viscosity": "Droplet Viscosity [Pa*s]",
    "left_substrate_density": "Left Sub. Density [kg/m^3]",
    "left_substrate_heat_capacity": "Left Sub. Heat Cap. [J/(kg*K)]",
    "left_substrate_thermal_conductivity": "Left Sub. Therm. Cond. [W/(m*K)]",
    "right_substrate_density": "Right Sub. Density [kg/m^3]",
    "right_substrate_heat_capacity": "Right Sub. Heat Cap. [J/(kg*K)]",
    "right_substrate_thermal_conductivity": "Right Sub. Therm. Cond. [W/(m*K)]",
    "left_substrate_temperature": "Left Sub. Temperature [K]",
    "right_substrate_temperature": "Right Sub. Temperature [K]",
    "left_contact_angle": "Left Contact Angle [deg]",
    "right_contact_angle": "Right Contact Angle [deg]",
}

SHORT_NAMES = {
    "surface_tension": "Surface Tension",
    "droplet_density": "Droplet Density",
    "droplet_viscosity": "Droplet Viscosity",
    "left_substrate_density": "L-Sub Density",
    "left_substrate_heat_capacity": "L-Sub Heat Cap",
    "left_substrate_thermal_conductivity": "L-Sub Therm Cond",
    "right_substrate_density": "R-Sub Density",
    "right_substrate_heat_capacity": "R-Sub Heat Cap",
    "right_substrate_thermal_conductivity": "R-Sub Therm Cond",
    "left_substrate_temperature": "L-Sub Temp",
    "right_substrate_temperature": "R-Sub Temp",
    "left_contact_angle": "L-Contact Angle",
    "right_contact_angle": "R-Contact Angle",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_bayesian_data(workspace_dir: str) -> pd.DataFrame:
    """Load all Bayesian experiment trace CSV files."""
    pattern = os.path.join(os.path.abspath(workspace_dir), TRACE_GLOB)
    csv_paths = sorted(glob.glob(pattern))
    if not csv_paths:
        raise FileNotFoundError(f"No trace files found: {pattern}")

    frames = []
    for path in csv_paths:
        exp_id = os.path.basename(os.path.dirname(os.path.dirname(path)))
        try:
            df = pd.read_csv(path)
            if df.empty:
                continue
            df["experiment_id"] = exp_id
            frames.append(df)
        except Exception:
            continue

    if not frames:
        raise RuntimeError("No valid Bayesian trace data.")
    merged = pd.concat(frames, ignore_index=True)
    print(f"[Bayesian] Loaded {len(merged)} evaluations from {len(frames)} experiments")
    return merged


def load_pso_data(batch_results_path: str) -> pd.DataFrame:
    """Load PSO batch_results CSV (best_params + best_error per experiment)."""
    df = pd.read_csv(batch_results_path)

    # Filter only successful/converged experiments
    df = df[df["status"].isin(["success"])].copy()
    df = df[df["best_error"] < 1e5].copy()

    # Parse best_params_json into columns
    param_records = []
    for _, row in df.iterrows():
        try:
            params = json.loads(row["best_params_json"])
            rec = {
                "experiment_id": str(row.get("experiment_id", "?")),
                "error": float(row["best_error"]),
            }
            rec.update(params)
            param_records.append(rec)
        except Exception:
            continue

    result = pd.DataFrame(param_records)
    print(f"[PSO] Loaded {len(result)} best-param rows from batch_results")
    return result


def get_param_columns(df: pd.DataFrame) -> List[str]:
    """Return ordered parameter columns."""
    all_cols = [c for c in df.columns if c not in META_COLUMNS and c != "experiment_id"]
    searchable = sorted([c for c in all_cols if c not in LOCKED_PARAMETERS])
    locked = sorted([c for c in all_cols if c in LOCKED_PARAMETERS])
    return list(searchable) + list(locked)


def filter_valid(df: pd.DataFrame, param_cols: List[str]) -> pd.DataFrame:
    """Keep successful rows with valid error."""
    filtered = df.copy()
    if "status" in filtered.columns:
        filtered = filtered[filtered["status"] == "success"]
    filtered = filtered.dropna(subset=[c for c in param_cols if c in filtered.columns] + ["error"])
    filtered = filtered[filtered["error"] < 1e5]
    return filtered


# ---------------------------------------------------------------------------
# Surrogate model & importance
# ---------------------------------------------------------------------------

def fit_surrogate(x, y, random_state=42, n_estimators=300):
    model = RandomForestRegressor(
        n_estimators=min(n_estimators, max(50, len(x) // 2)),
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    model.fit(x, y)
    r2 = model.score(x, y)
    print(f"  RF surrogate R^2 = {r2:.4f} (n={len(x)})")
    return model


def compute_importance(model, x, y) -> pd.DataFrame:
    result = permutation_importance(
        model, x, y, n_repeats=50, random_state=42, n_jobs=-1,
        scoring="neg_mean_absolute_error",
    )
    df = pd.DataFrame({
        "parameter": list(x.columns),
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values("importance_mean", ascending=False).reset_index(drop=True)
    total = df["importance_mean"].sum()
    if total > 0:
        df["importance_pct"] = (df["importance_mean"] / total * 100).round(2)
    return df


def compute_local_sensitivity(model, x, param_cols, reference_row, n_grid=50):
    records = []
    for col in param_cols:
        col_min = float(x[col].min())
        col_max = float(x[col].max())
        grid = np.linspace(col_min, col_max, n_grid)
        sweep = pd.DataFrame([reference_row.values] * n_grid, columns=x.columns)
        sweep[col] = grid
        pred = model.predict(sweep)
        for g, p in zip(grid, pred):
            records.append({
                "parameter": col,
                "parameter_value": float(g),
                "predicted_error": float(p),
                "reference_value": float(reference_row[col]),
            })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Comparison plots
# ---------------------------------------------------------------------------

def plot_importance_comparison(
    bayesian_imp: pd.DataFrame,
    pso_imp: pd.DataFrame,
    output_dir: str,
):
    """Side-by-side horizontal bar chart: Bayesian vs PSO importance."""
    # Normalize both to 100%
    def _norm(df):
        total = df["importance_mean"].sum()
        if total > 0:
            df = df.copy()
            df["importance_pct"] = (df["importance_mean"] / total * 100).round(1)
        return df

    b_imp = _norm(bayesian_imp).sort_values("importance_mean", ascending=True)
    p_imp = _norm(pso_imp).sort_values("importance_mean", ascending=True)

    # Ensure same parameter ordering by averaging ranks
    all_params = list(dict.fromkeys(
        list(b_imp["parameter"]) + list(p_imp["parameter"])
    ))
    # Sort by average importance
    avg_imp = {}
    for p in all_params:
        b_val = b_imp.loc[b_imp["parameter"] == p, "importance_pct"]
        p_val = p_imp.loc[p_imp["parameter"] == p, "importance_pct"]
        avg_imp[p] = (
            (float(b_val.iloc[0]) if len(b_val) > 0 else 0) +
            (float(p_val.iloc[0]) if len(p_val) > 0 else 0)
        ) / 2
    sorted_params = sorted(all_params, key=lambda p: avg_imp.get(p, 0), reverse=False)

    n = len(sorted_params)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, max(6, 0.45 * n)), sharey=True)

    def _draw_bar(ax, df, title, color):
        df = df.set_index("parameter")
        rows = []
        for p in sorted_params:
            if p in df.index:
                rows.append({
                    "parameter": p,
                    "importance_mean": float(df.loc[p, "importance_mean"]),
                    "importance_std": float(df.loc[p, "importance_std"]),
                    "importance_pct": float(df.loc[p, "importance_pct"]),
                })
            else:
                rows.append({
                    "parameter": p,
                    "importance_mean": 0.0,
                    "importance_std": 0.0,
                    "importance_pct": 0.0,
                })
        plot_df = pd.DataFrame(rows)
        bar_colors = [
            "#d62728" if p in LOCKED_PARAMETERS else color
            for p in plot_df["parameter"]
        ]
        bars = ax.barh(
            plot_df["parameter"].map(lambda p: SHORT_NAMES.get(p, p)),
            plot_df["importance_mean"],
            xerr=plot_df["importance_std"],
            color=bar_colors,
            edgecolor="white",
            linewidth=0.5,
        )
        max_w = plot_df["importance_mean"].max() or 1
        for bar, (_, row) in zip(bars, plot_df.iterrows()):
            pct = row.get("importance_pct", 0)
            ax.text(
                bar.get_width() + 0.003 * max_w,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%",
                va="center", fontsize=8, color="#333",
            )
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Permutation Importance (MAE increase)", fontsize=10)
        ax.grid(axis="x", alpha=0.3)
        ax.set_xlim(0, max_w * 1.25)

    _draw_bar(ax1, b_imp, f"Bayesian (n={len(bayesian_imp)} params)", "#1f77b4")
    _draw_bar(ax2, p_imp, f"PSO (n={len(pso_imp)} params)", "#ff7f0e")

    fig.suptitle("Parameter Importance Comparison: Bayesian vs PSO",
                 fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()

    path = os.path.join(output_dir, "comparison_importance_bayesian_vs_pso.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] Importance comparison: {path}")
    return path


def plot_sensitivity_comparison(
    bayesian_curves: pd.DataFrame,
    pso_curves: pd.DataFrame,
    param_cols: List[str],
    output_dir: str,
):
    """Overlay Bayesian and PSO sensitivity curves on same subplots."""
    n_features = len(param_cols)
    n_cols = 3
    n_rows = int(np.ceil(n_features / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 3.6 * n_rows))
    axes = np.atleast_1d(axes).flatten()

    for i, col in enumerate(param_cols):
        ax = axes[i]
        disp = SHORT_NAMES.get(col, col)

        # Bayesian curve
        b_sub = bayesian_curves[bayesian_curves["parameter"] == col] if bayesian_curves is not None else pd.DataFrame()
        if not b_sub.empty:
            ax.plot(b_sub["parameter_value"], b_sub["predicted_error"],
                    linewidth=2, color="#1f77b4", label="Bayesian", alpha=0.85)
            b_min_idx = int(np.argmin(b_sub["predicted_error"].values))
            ax.scatter(b_sub["parameter_value"].iloc[b_min_idx],
                       b_sub["predicted_error"].iloc[b_min_idx],
                       color="#1f77b4", s=40, zorder=5, marker="o")

        # PSO curve
        p_sub = pso_curves[pso_curves["parameter"] == col] if pso_curves is not None else pd.DataFrame()
        if not p_sub.empty:
            ax.plot(p_sub["parameter_value"], p_sub["predicted_error"],
                    linewidth=2, color="#ff7f0e", label="PSO", alpha=0.85, linestyle="--")
            p_min_idx = int(np.argmin(p_sub["predicted_error"].values))
            ax.scatter(p_sub["parameter_value"].iloc[p_min_idx],
                       p_sub["predicted_error"].iloc[p_min_idx],
                       color="#ff7f0e", s=40, zorder=5, marker="s")

        ax.set_title(disp, fontsize=10, fontweight="bold")
        ax.set_xlabel("Parameter Value", fontsize=8)
        ax.set_ylabel("Predicted Error [deg]", fontsize=8)
        ax.grid(alpha=0.3)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, loc="upper right")

    for j in range(n_features, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Local Sensitivity Comparison: Bayesian (solid) vs PSO (dashed)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    path = os.path.join(output_dir, "comparison_sensitivity_bayesian_vs_pso.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] Sensitivity comparison: {path}")
    return path


def plot_importance_ranking_comparison(
    bayesian_imp: pd.DataFrame,
    pso_imp: pd.DataFrame,
    output_dir: str,
):
    """Dot/cross comparison: point = Bayesian imp%, cross = PSO imp%."""
    def _norm(df):
        total = df["importance_mean"].sum()
        if total > 0:
            df = df.copy()
            df["importance_pct"] = (df["importance_mean"] / total * 100).round(1)
        return df
    b_imp = _norm(bayesian_imp)
    p_imp = _norm(pso_imp)

    all_params = sorted(set(list(b_imp["parameter"]) + list(p_imp["parameter"])),
                        key=lambda p: max(
                            float(b_imp.loc[b_imp["parameter"] == p, "importance_pct"].iloc[0]) if p in b_imp["parameter"].values else 0,
                            float(p_imp.loc[p_imp["parameter"] == p, "importance_pct"].iloc[0]) if p in p_imp["parameter"].values else 0,
                        ), reverse=True)

    n = len(all_params)
    b_vals = []
    p_vals = []
    labels = []
    for p in all_params:
        labels.append(SHORT_NAMES.get(p, p))
        b_vals.append(float(b_imp.loc[b_imp["parameter"] == p, "importance_pct"].iloc[0]) if p in b_imp["parameter"].values else 0)
        p_vals.append(float(p_imp.loc[p_imp["parameter"] == p, "importance_pct"].iloc[0]) if p in p_imp["parameter"].values else 0)

    fig, ax = plt.subplots(figsize=(14, max(5, 0.4 * n)))
    y = np.arange(n)

    # Bars for Bayesian
    bars_b = ax.barh(y + 0.2, b_vals, height=0.35, color="#1f77b4", alpha=0.85, label="Bayesian")
    bars_p = ax.barh(y - 0.2, p_vals, height=0.35, color="#ff7f0e", alpha=0.85, label="PSO")

    # Annotate
    for bar, val in zip(bars_b, b_vals):
        if val > 0:
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", fontsize=8, color="#1f77b4")
    for bar, val in zip(bars_p, p_vals):
        if val > 0:
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", fontsize=8, color="#ff7f0e")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Importance (%)", fontsize=11)
    ax.set_title("Parameter Importance Ranking: Bayesian vs PSO",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(0, max(max(b_vals), max(p_vals)) * 1.3)

    plt.tight_layout()
    path = os.path.join(output_dir, "comparison_ranking_bayesian_vs_pso.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] Ranking comparison: {path}")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Bayesian vs PSO sensitivity comparison")
    parser.add_argument("--workspace-dir", type=str, default="./simulation_workspace",
                        help="Workspace directory containing exp_*/ and batch_results_full2/")
    parser.add_argument("--pso-batch", type=str, default=None,
                        help="Path to PSO batch_results.csv. Default: <workspace-dir>/batch_results_full2/batch_results.csv")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory. Default: <workspace-dir>/sensitivity_comparison")
    args = parser.parse_args()

    workspace_dir = os.path.abspath(args.workspace_dir)
    output_dir = os.path.abspath(
        args.output_dir or os.path.join(workspace_dir, "sensitivity_comparison")
    )
    os.makedirs(output_dir, exist_ok=True)

    pso_batch_path = args.pso_batch or os.path.join(workspace_dir, "batch_results_full2", "batch_results.csv")
    if not os.path.exists(pso_batch_path):
        print(f"[ERROR] PSO batch results not found: {pso_batch_path}")
        return 1

    print("=" * 70)
    print("Sensitivity Analysis Comparison: Bayesian vs PSO")
    print("=" * 70)
    print(f"Workspace: {workspace_dir}")
    print(f"PSO batch: {pso_batch_path}")
    print(f"Output:    {output_dir}")

    # ---- Load data ----
    # 1. Bayesian (full traces)
    df_bayes = load_bayesian_data(workspace_dir)
    param_cols_all = get_param_columns(df_bayes)
    print(f"  Parameters: {param_cols_all}")

    valid_bayes = filter_valid(df_bayes, param_cols_all)
    if valid_bayes.empty:
        print("[ERROR] No valid Bayesian data after filtering.")
        return 1

    # 2. PSO (batch_results)
    df_pso_raw = load_pso_data(pso_batch_path)
    # Ensure consistent param columns with Bayesian
    pso_param_cols = [c for c in param_cols_all if c in df_pso_raw.columns]
    if not pso_param_cols:
        print("[ERROR] No matching parameter columns in PSO data.")
        return 1
    valid_pso = df_pso_raw.dropna(subset=pso_param_cols + ["error"])
    valid_pso = valid_pso[valid_pso["error"] < 1e5]
    print(f"[PSO] {len(valid_pso)} valid rows after filtering")

    # ---- Bayesian analysis ----
    print("\n--- Bayesian Sensitivity Analysis ---")
    x_b = valid_bayes[param_cols_all]
    y_b = valid_bayes["error"]
    model_b = fit_surrogate(x_b, y_b)
    imp_b = compute_importance(model_b, x_b, y_b)
    imp_b.to_csv(os.path.join(output_dir, "importance_bayesian.csv"), index=False, encoding="utf-8")

    best_idx_b = int(np.argmin(y_b.values))
    ref_b = x_b.iloc[best_idx_b]
    curves_b = compute_local_sensitivity(model_b, x_b, param_cols_all, reference_row=ref_b)
    curves_b.to_csv(os.path.join(output_dir, "sensitivity_bayesian.csv"), index=False, encoding="utf-8")

    # ---- PSO analysis ----
    print("\n--- PSO Sensitivity Analysis ---")
    x_p = valid_pso[pso_param_cols].astype(float)
    y_p = valid_pso["error"].astype(float)
    model_p = fit_surrogate(x_p, y_p, n_estimators=min(200, len(x_p) // 2))
    imp_p = compute_importance(model_p, x_p, y_p)
    imp_p.to_csv(os.path.join(output_dir, "importance_pso.csv"), index=False, encoding="utf-8")

    best_idx_p = int(np.argmin(y_p.values))
    ref_p = x_p.iloc[best_idx_p]
    curves_p = compute_local_sensitivity(model_p, x_p, pso_param_cols, reference_row=ref_p)

    # ---- Comparison plots ----
    print("\n--- Generating Comparison Plots ---")

    # 1. Side-by-side importance (horizontal bars)
    plot_importance_comparison(imp_b, imp_p, output_dir)

    # 2. Sensitivity curves overlay
    common_cols = sorted(set(param_cols_all) & set(pso_param_cols),
                         key=lambda c: param_cols_all.index(c) if c in param_cols_all else 99)
    plot_sensitivity_comparison(curves_b, curves_p, common_cols, output_dir)

    # 3. Ranking comparison (grouped bar chart)
    plot_importance_ranking_comparison(imp_b, imp_p, output_dir)

    # ---- Summary table ----
    summary_rows = []
    for p in common_cols:
        b_row = imp_b[imp_b["parameter"] == p]
        p_row = imp_p[imp_p["parameter"] == p]
        b_pct = float(b_row["importance_pct"].iloc[0]) if len(b_row) > 0 else 0.0
        p_pct = float(p_row["importance_pct"].iloc[0]) if len(p_row) > 0 else 0.0
        b_mean = float(b_row["importance_mean"].iloc[0]) if len(b_row) > 0 else 0.0
        p_mean = float(p_row["importance_mean"].iloc[0]) if len(p_row) > 0 else 0.0
        summary_rows.append({
            "parameter": p,
            "display_name": SHORT_NAMES.get(p, p),
            "bayesian_imp_pct": b_pct,
            "pso_imp_pct": p_pct,
            "diff_pct": round(p_pct - b_pct, 2),
            "bayesian_imp_raw": round(b_mean, 6),
            "pso_imp_raw": round(p_mean, 6),
        })
    summary = pd.DataFrame(summary_rows).sort_values("bayesian_imp_pct", ascending=False)
    summary_path = os.path.join(output_dir, "comparison_summary.csv")
    summary.to_csv(summary_path, index=False, encoding="utf-8")
    print(f"[Output] Summary CSV: {summary_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"\n{'Parameter':<35} {'Bayesian%':>10} {'PSO%':>10} {'Diff':>8}")
    print("-" * 70)
    for _, row in summary.iterrows():
        print(f"{row['display_name']:<35} {row['bayesian_imp_pct']:>9.1f}% {row['pso_imp_pct']:>9.1f}% {row['diff_pct']:>+7.1f}%")
    print(f"\nAll outputs: {output_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
