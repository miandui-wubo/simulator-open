#!/usr/bin/env python3
"""
Comprehensive parameter sensitivity analysis for Bayesian optimization experiments.

Aggregates all experiment optimization traces and produces:
  1. Global importance ranking (permutation importance via Random Forest)
  2. Local sensitivity curves (one-parameter sweep around best point)
  3. Per-experiment breakdown (for experiments with sufficient data)

Outputs are saved to simulation_workspace/sensitivity_analysis/

Usage:
    python -m simulator.sensitivity_analysis
    python -m simulator.sensitivity_analysis --workspace-dir ./simulation_workspace
    python -m simulator.sensitivity_analysis --output-dir ./my_analysis
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRACE_GLOB = "exp_*/optimization_trace/optimization_trace.csv"

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

# Parameters that are locked to experimental values (not free to search)
LOCKED_PARAMETERS = {
    "left_substrate_temperature",
    "right_substrate_temperature",
}

# Pretty display names for plot labels
PARAM_DISPLAY_NAMES = {
    "surface_tension": "Surface Tension [N/m]",
    "droplet_density": "Droplet Density [kg/m^3]",
    "droplet_viscosity": "Droplet Viscosity [Pa*s]",
    "left_substrate_density": "Left Sub. Density [kg/m^3]",
    "left_substrate_heat_capacity": "Left Sub. Heat Capacity [J/(kg*K)]",
    "left_substrate_thermal_conductivity": "Left Sub. Therm. Conduct. [W/(m*K)]",
    "right_substrate_density": "Right Sub. Density [kg/m^3]",
    "right_substrate_heat_capacity": "Right Sub. Heat Capacity [J/(kg*K)]",
    "right_substrate_thermal_conductivity": "Right Sub. Therm. Conduct. [W/(m*K)]",
    "left_substrate_temperature": "Left Sub. Temperature [K]",
    "right_substrate_temperature": "Right Sub. Temperature [K]",
    "left_contact_angle": "Left Contact Angle [deg]",
    "right_contact_angle": "Right Contact Angle [deg]",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_all_traces(workspace_dir: str) -> pd.DataFrame:
    """Load and merge all experiment optimization traces."""
    pattern = os.path.join(os.path.abspath(workspace_dir), TRACE_GLOB)
    csv_paths = sorted(glob.glob(pattern))
    if not csv_paths:
        raise FileNotFoundError(f"No trace files found matching: {pattern}")

    frames = []
    for path in csv_paths:
        exp_id = os.path.basename(os.path.dirname(os.path.dirname(path)))
        try:
            df = pd.read_csv(path)
            if df.empty:
                print(f"  [WARN] {exp_id}: empty trace, skipping")
                continue
            df["experiment_id"] = exp_id
            frames.append(df)
        except Exception as exc:
            print(f"  [WARN] {exp_id}: failed to read ({exc}), skipping")

    if not frames:
        raise RuntimeError("No valid trace data loaded.")

    merged = pd.concat(frames, ignore_index=True)
    print(f"[Data] Loaded {len(merged)} evaluations from {len(frames)} experiments")
    return merged


def get_param_columns(df: pd.DataFrame) -> List[str]:
    """Return ordered list of parameter columns."""
    all_cols = [c for c in df.columns if c not in META_COLUMNS and c != "experiment_id"]
    # Sort to have a consistent order: searchable params first, locked last
    searchable = sorted([c for c in all_cols if c not in LOCKED_PARAMETERS])
    locked = sorted([c for c in all_cols if c in LOCKED_PARAMETERS])
    return searchable + locked


def filter_valid(df: pd.DataFrame, param_cols: List[str]) -> pd.DataFrame:
    """Keep only successful evaluations with valid error values."""
    filtered = df.copy()
    if "status" in filtered.columns:
        filtered = filtered[filtered["status"] == "success"]
    filtered = filtered.dropna(subset=param_cols + ["error"])
    # Remove penalty/fallback errors (1e6)
    filtered = filtered[filtered["error"] < 1e5]
    if filtered.empty:
        raise RuntimeError("No valid successful evaluations after filtering.")
    print(f"[Data] {len(filtered)} valid evaluations after filtering (removed failures & penalties)")
    return filtered


# ---------------------------------------------------------------------------
# Surrogate model
# ---------------------------------------------------------------------------


def fit_surrogate(x: pd.DataFrame, y: pd.Series, random_state: int = 42) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=400,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    model.fit(x, y)
    # Report training R^2
    r2 = model.score(x, y)
    print(f"[Model] RF surrogate R^2 = {r2:.4f}")
    return model


# ---------------------------------------------------------------------------
# Global importance
# ---------------------------------------------------------------------------


def compute_global_importance(
    model: RandomForestRegressor,
    x: pd.DataFrame,
    y: pd.Series,
) -> pd.DataFrame:
    result = permutation_importance(
        model, x, y,
        n_repeats=50,
        random_state=42,
        n_jobs=-1,
        scoring="neg_mean_absolute_error",
    )
    df = pd.DataFrame({
        "parameter": x.columns,
        "importance_mean": result.importances_mean,
        "importance_std": result.importances_std,
    }).sort_values("importance_mean", ascending=False).reset_index(drop=True)

    # Normalize to percentage of total
    total = df["importance_mean"].sum()
    if total > 0:
        df["importance_pct"] = (df["importance_mean"] / total * 100).round(2)

    return df


def plot_global_importance(importance_df: pd.DataFrame, output_dir: str, tag: str = "") -> str:
    """Horizontal bar chart, sorted by importance."""
    df = importance_df.sort_values("importance_mean", ascending=True)
    n = len(df)

    fig, ax = plt.subplots(figsize=(12, max(5, 0.45 * n)))
    colors = [
        "#d62728" if p in LOCKED_PARAMETERS else "#1f77b4"
        for p in df["parameter"]
    ]
    bars = ax.barh(
        df["parameter"].map(lambda p: PARAM_DISPLAY_NAMES.get(p, p)),
        df["importance_mean"],
        xerr=df["importance_std"],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )
    # Annotate percentage
    for bar, (_, row) in zip(bars, df.iterrows()):
        pct = row.get("importance_pct", 0)
        ax.text(
            bar.get_width() + 0.002 * df["importance_mean"].max(),
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%",
            va="center",
            fontsize=9,
            color="#333333",
        )

    ax.set_xlabel("Permutation Importance (MAE increase)", fontsize=12)
    ax.set_title(
        f"Global Parameter Importance Ranking\n({tag} - {len(df)} parameters, RF surrogate)",
        fontsize=13,
        fontweight="bold",
    )
    ax.grid(axis="x", alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#1f77b4", label="Searchable"),
        Patch(facecolor="#d62728", label="Locked (temperature)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    plt.tight_layout()
    path = os.path.join(output_dir, f"global_importance_ranking{'_' + tag if tag else ''}.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] Global importance chart: {path}")
    return path


# ---------------------------------------------------------------------------
# Local sensitivity curves
# ---------------------------------------------------------------------------


def compute_local_sensitivity(
    model: RandomForestRegressor,
    x: pd.DataFrame,
    param_cols: List[str],
    reference_row: Optional[pd.Series] = None,
    n_grid: int = 100,
) -> pd.DataFrame:
    """One-parameter sweep around reference (best) point."""
    if reference_row is None:
        best_idx = int(np.argmin(model.predict(x)))
        reference_row = x.iloc[best_idx].copy()
        print(f"[Sensitivity] Using best sample as reference (index={best_idx})")

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


def plot_local_sensitivity_curves(
    curve_df: pd.DataFrame,
    x: pd.DataFrame,
    param_cols: List[str],
    reference_row: pd.Series,
    output_dir: str,
    tag: str = "",
) -> str:
    """Grid of one-parameter sensitivity curves."""
    n_features = len(param_cols)
    n_cols = 3
    n_rows = int(np.ceil(n_features / n_cols))

    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(5.5 * n_cols, 3.8 * n_rows),
    )
    axes = np.atleast_1d(axes).flatten()

    for i, col in enumerate(param_cols):
        sub = curve_df[curve_df["parameter"] == col]
        ref_val = float(reference_row[col])
        disp_name = PARAM_DISPLAY_NAMES.get(col, col)

        ax = axes[i]
        ax.plot(
            sub["parameter_value"],
            sub["predicted_error"],
            linewidth=2,
            color="#1f77b4",
        )
        ax.axvline(ref_val, linestyle="--", linewidth=1.2, color="#d62728", alpha=0.8)
        # Mark the minimum predicted error
        min_idx = int(np.argmin(sub["predicted_error"].values))
        ax.scatter(
            sub["parameter_value"].iloc[min_idx],
            sub["predicted_error"].iloc[min_idx],
            color="#d62728",
            s=30,
            zorder=5,
        )

        ax.set_title(disp_name, fontsize=10, fontweight="bold")
        ax.set_xlabel(disp_name, fontsize=8)
        ax.set_ylabel("Predicted Error [deg]", fontsize=8)
        ax.grid(alpha=0.3)
        ax.tick_params(labelsize=7)

    # Hide unused subplots
    for j in range(n_features, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(
        f"Local Sensitivity Curves - One-Parameter Sweep\n"
        f"({tag} - RF surrogate, red=reference, dot=minimum)",
        fontsize=13,
        fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    path = os.path.join(output_dir, f"local_sensitivity_curves{'_' + tag if tag else ''}.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] Local sensitivity curves: {path}")
    return path


# ---------------------------------------------------------------------------
# Per-experiment analysis
# ---------------------------------------------------------------------------


def analyze_per_experiment(
    df: pd.DataFrame,
    param_cols: List[str],
    output_dir: str,
    min_evaluations: int = 8,
) -> None:
    """Run importance + sensitivity per experiment (if sufficient data)."""
    sub_dir = os.path.join(output_dir, "per_experiment")
    os.makedirs(sub_dir, exist_ok=True)

    exp_ids = sorted(df["experiment_id"].unique())
    for exp_id in exp_ids:
        sub = df[df["experiment_id"] == exp_id].copy()
        sub = sub.dropna(subset=param_cols + ["error"])
        sub = sub[sub["error"] < 1e5]

        # Locked params have zero variance within an experiment - drop them
        active_params = [
            c for c in param_cols
            if c not in LOCKED_PARAMETERS or sub[c].nunique() > 1
        ]
        if len(active_params) < 2 or len(sub) < min_evaluations:
            continue

        x = sub[active_params]
        y = sub["error"]
        try:
            model = fit_surrogate(x, y)
        except Exception as exc:
            print(f"  [WARN] {exp_id}: surrogate fit failed: {exc}")
            continue

        # Global importance
        imp = compute_global_importance(model, x, y)
        imp.to_csv(
            os.path.join(sub_dir, f"{exp_id}_importance.csv"),
            index=False, encoding="utf-8",
        )
        plot_global_importance(imp, sub_dir, tag=exp_id)

        # Local sensitivity
        best_idx = int(np.argmin(y.values))
        ref = x.iloc[best_idx]
        curves = compute_local_sensitivity(model, x, active_params, reference_row=ref)
        curves.to_csv(
            os.path.join(sub_dir, f"{exp_id}_sensitivity.csv"),
            index=False, encoding="utf-8",
        )
        plot_local_sensitivity_curves(curves, x, active_params, ref, sub_dir, tag=exp_id)


# ---------------------------------------------------------------------------
# Summary: aggregated importance across experiments
# ---------------------------------------------------------------------------


def analyze_aggregated_importance(
    df: pd.DataFrame,
    param_cols: List[str],
    output_dir: str,
) -> None:
    """
    For each experiment, compute permutation importance.
    Then aggregate mean ± std across experiments.
    """
    exp_ids = sorted(df["experiment_id"].unique())
    all_imps: Dict[str, List[float]] = {p: [] for p in param_cols}

    for exp_id in exp_ids:
        sub = df[df["experiment_id"] == exp_id].copy()
        sub = sub.dropna(subset=param_cols + ["error"])
        sub = sub[sub["error"] < 1e5]
        if len(sub) < 5:
            continue

        active = [c for c in param_cols if sub[c].nunique() > 1]
        if len(active) < 2:
            continue

        x = sub[active]
        y = sub["error"]
        try:
            model = fit_surrogate(x, y)
            result = permutation_importance(
                model, x, y,
                n_repeats=20,
                random_state=42,
                n_jobs=-1,
                scoring="neg_mean_absolute_error",
            )
            for col, imp_val in zip(active, result.importances_mean):
                all_imps[col].append(imp_val)
        except Exception:
            continue

    records = []
    for p in param_cols:
        vals = all_imps.get(p, [])
        if vals:
            records.append({
                "parameter": p,
                "importance_mean": float(np.mean(vals)),
                "importance_std": float(np.std(vals)),
                "n_experiments": len(vals),
            })
        else:
            records.append({
                "parameter": p,
                "importance_mean": 0.0,
                "importance_std": 0.0,
                "n_experiments": 0,
            })

    agg_df = pd.DataFrame(records).sort_values("importance_mean", ascending=False)
    total = agg_df["importance_mean"].sum()
    if total > 0:
        agg_df["importance_pct"] = (agg_df["importance_mean"] / total * 100).round(2)

    csv_path = os.path.join(output_dir, "aggregated_importance_ranking.csv")
    agg_df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[Output] Aggregated importance CSV: {csv_path}")

    # Plot
    plot_df = agg_df[agg_df["importance_mean"] > 0].sort_values("importance_mean", ascending=True)
    if plot_df.empty:
        print("[WARN] No nonzero importance values for aggregated plot, skipping.")
        return

    n = len(plot_df)
    fig, ax = plt.subplots(figsize=(12, max(5, 0.45 * n)))
    colors = ["#d62728" if p in LOCKED_PARAMETERS else "#1f77b4" for p in plot_df["parameter"]]
    bars = ax.barh(
        plot_df["parameter"].map(lambda p: PARAM_DISPLAY_NAMES.get(p, p)),
        plot_df["importance_mean"],
        xerr=plot_df["importance_std"],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )
    for bar, (_, row) in zip(bars, plot_df.iterrows()):
        pct = row.get("importance_pct", 0)
        ax.text(
            bar.get_width() + 0.002 * plot_df["importance_mean"].max(),
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%",
            va="center",
            fontsize=9,
            color="#333333",
        )

    ax.set_xlabel("Mean Permutation Importance (across experiments)", fontsize=12)
    ax.set_title(
        f"Aggregated Parameter Importance Ranking\n"
        f"(mean {chr(0x00B1)} std across {len(exp_ids)} experiments)",
        fontsize=13, fontweight="bold",
    )
    ax.grid(axis="x", alpha=0.3)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#1f77b4", label="Searchable"),
        Patch(facecolor="#d62728", label="Locked (temperature)"),
    ], loc="lower right")

    plt.tight_layout()
    png_path = os.path.join(output_dir, "aggregated_importance_ranking.png")
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] Aggregated importance chart: {png_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Comprehensive sensitivity analysis for Bayesian optimization"
    )
    parser.add_argument(
        "--workspace-dir",
        type=str,
        default="./simulation_workspace",
        help="Workspace directory containing exp_*/optimization_trace/ subdirs.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory. Default: <workspace-dir>/sensitivity_analysis",
    )
    parser.add_argument(
        "--min-evaluations",
        type=int,
        default=8,
        help="Minimum evaluations for per-experiment analysis (default: 8).",
    )
    parser.add_argument(
        "--skip-per-experiment",
        action="store_true",
        help="Skip per-experiment breakdown.",
    )
    args = parser.parse_args()

    workspace_dir = os.path.abspath(args.workspace_dir)
    output_dir = os.path.abspath(
        args.output_dir or os.path.join(workspace_dir, "sensitivity_analysis")
    )
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("Sensitivity Analysis for Bayesian Optimization Results")
    print("=" * 70)
    print(f"Workspace: {workspace_dir}")
    print(f"Output:    {output_dir}")

    # ---- Load & prepare data ----
    df = load_all_traces(workspace_dir)
    param_cols = get_param_columns(df)
    print(f"[Data] Parameter columns ({len(param_cols)}): {param_cols}")

    valid = filter_valid(df, param_cols)
    x = valid[param_cols]
    y = valid["error"]

    # ---- 1. Combined global importance ----
    print("\n" + "-" * 50)
    print("Step 1: Combined Global Importance (all experiments)")
    print("-" * 50)
    model = fit_surrogate(x, y)
    importance_df = compute_global_importance(model, x, y)
    importance_df.to_csv(
        os.path.join(output_dir, "combined_importance_ranking.csv"),
        index=False, encoding="utf-8",
    )
    plot_global_importance(importance_df, output_dir, tag="combined")

    # ---- 2. Combined local sensitivity ----
    print("\n" + "-" * 50)
    print("Step 2: Combined Local Sensitivity Curves")
    print("-" * 50)
    best_idx = int(np.argmin(y.values))
    reference_row = x.iloc[best_idx]
    print(f"[Sensitivity] Reference: experiment={valid['experiment_id'].iloc[best_idx]}, "
          f"error={y.iloc[best_idx]:.4f}")

    curves = compute_local_sensitivity(model, x, param_cols, reference_row=reference_row)
    curves.to_csv(
        os.path.join(output_dir, "combined_local_sensitivity.csv"),
        index=False, encoding="utf-8",
    )
    plot_local_sensitivity_curves(curves, x, param_cols, reference_row, output_dir, tag="combined")

    # ---- 3. Aggregated per-experiment importance ----
    print("\n" + "-" * 50)
    print("Step 3: Aggregated Importance Across Experiments")
    print("-" * 50)
    analyze_aggregated_importance(df, param_cols, output_dir)

    # ---- 4. Per-experiment analysis ----
    if not args.skip_per_experiment:
        print("\n" + "-" * 50)
        print("Step 4: Per-Experiment Analysis")
        print("-" * 50)
        analyze_per_experiment(df, param_cols, output_dir, min_evaluations=args.min_evaluations)

    # ---- Summary ----
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"Combined importance:     {os.path.join(output_dir, 'combined_importance_ranking.csv')}")
    print(f"Combined importance PNG: {os.path.join(output_dir, 'global_importance_ranking_combined.png')}")
    print(f"Combined sensitivity:    {os.path.join(output_dir, 'combined_local_sensitivity.csv')}")
    print(f"Combined sensitivity PNG:{os.path.join(output_dir, 'local_sensitivity_curves_combined.png')}")
    print(f"Aggregated importance:   {os.path.join(output_dir, 'aggregated_importance_ranking.csv')}")
    print(f"Aggregated importance PNG:{os.path.join(output_dir, 'aggregated_importance_ranking.png')}")
    if not args.skip_per_experiment:
        print(f"Per-experiment:          {os.path.join(output_dir, 'per_experiment/')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
