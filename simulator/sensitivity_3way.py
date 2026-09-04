#!/usr/bin/env python3
"""
Three-way sensitivity comparison: Bayesian vs PSO vs GA.

Data sources:
  - Bayesian: <workspace>/exp_*/optimization_trace/optimization_trace.csv
  - PSO:      <workspace>/batch_results_full2/batch_results.csv
  - GA:       <workspace>/batch_results_ga/batch_results.csv
              + <workspace>/batch_results_ga_resume/batch_results.csv

Outputs (under <workspace>/sensitivity_comparison_3way/):
  - importance_{bayesian,pso,ga}.csv
  - sensitivity_{bayesian,pso,ga}.csv
  - three_way_importance_overlay.png   (3 algorithms on one shared axis)
  - three_way_importance_side_by_side.png
  - three_way_sensitivity_curves.png
  - three_way_summary.csv

Usage:
    python -m simulator.sensitivity_3way
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

# ---------------------------------------------------------------------------
# Constants (kept in sync with sensitivity_compare.py)
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

# Algorithm colors
ALGO_COLORS = {
    "Bayesian": "#1f77b4",
    "PSO": "#ff7f0e",
    "GA": "#2ca02c",
}
LOCKED_COLOR = "#d62728"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_bayesian_data(workspace_dir: str) -> pd.DataFrame:
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


def load_best_param_data(csv_paths: List[str], algo_name: str) -> pd.DataFrame:
    """Load best_params + best_error from one or more batch_results CSVs."""
    frames = []
    for p in csv_paths:
        if not os.path.exists(p):
            print(f"  [WARN] missing: {p}")
            continue
        df = pd.read_csv(p)
        df = df[df["status"].isin(["success"])].copy()
        df = df[df["best_error"].notna() & (df["best_error"] < 1e5)].copy()
        df["_source"] = os.path.basename(os.path.dirname(p))
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No valid batch_results for {algo_name}: {csv_paths}")
    df = pd.concat(frames, ignore_index=True)

    records = []
    for _, row in df.iterrows():
        try:
            params = json.loads(row["best_params_json"]) if row.get("best_params_json") else {}
        except Exception:
            continue
        rec = {
            "experiment_id": str(row.get("experiment_id", "?")),
            "error": float(row["best_error"]),
        }
        rec.update(params)
        records.append(rec)
    out = pd.DataFrame(records)
    print(f"[{algo_name}] Loaded {len(out)} best-param rows from {len(frames)} batch file(s)")
    return out


def get_param_columns(df: pd.DataFrame) -> List[str]:
    all_cols = [c for c in df.columns if c not in META_COLUMNS and c not in {"experiment_id", "_source"}]
    searchable = sorted([c for c in all_cols if c not in LOCKED_PARAMETERS])
    locked = sorted([c for c in all_cols if c in LOCKED_PARAMETERS])
    return list(searchable) + list(locked)


def filter_valid(df: pd.DataFrame, param_cols: List[str]) -> pd.DataFrame:
    filtered = df.copy()
    if "status" in filtered.columns:
        filtered = filtered[filtered["status"] == "success"]
    filtered = filtered.dropna(subset=[c for c in param_cols if c in filtered.columns] + ["error"])
    filtered = filtered[filtered["error"] < 1e5]
    return filtered


# ---------------------------------------------------------------------------
# Surrogate model & analysis
# ---------------------------------------------------------------------------

def fit_surrogate(x, y, random_state=42, n_estimators=300):
    n = len(x)
    model = RandomForestRegressor(
        n_estimators=min(n_estimators, max(50, n // 2)) if n < 200 else n_estimators,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    model.fit(x, y)
    r2 = model.score(x, y)
    print(f"  RF surrogate R^2 = {r2:.4f} (n={n})")
    return model


def compute_importance(model, x, y) -> pd.DataFrame:
    n_repeats = 50 if len(x) >= 100 else 25
    result = permutation_importance(
        model, x, y, n_repeats=n_repeats, random_state=42, n_jobs=-1,
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
        if col_min == col_max:
            continue
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


def run_algo(name: str, df: pd.DataFrame, param_cols: List[str], output_dir: str):
    print(f"\n--- {name} Sensitivity Analysis ---")
    valid = filter_valid(df, param_cols)
    if valid.empty:
        print(f"  [WARN] No valid rows for {name}")
        return None
    cols = [c for c in param_cols if c in valid.columns]
    x = valid[cols].astype(float)
    y = valid["error"].astype(float)
    model = fit_surrogate(x, y)
    imp = compute_importance(model, x, y)
    imp.to_csv(os.path.join(output_dir, f"importance_{name.lower()}.csv"),
               index=False, encoding="utf-8")
    best_idx = int(np.argmin(y.values))
    ref = x.iloc[best_idx]
    curves = compute_local_sensitivity(model, x, cols, reference_row=ref)
    curves.to_csv(os.path.join(output_dir, f"sensitivity_{name.lower()}.csv"),
                  index=False, encoding="utf-8")
    return {"name": name, "importance": imp, "curves": curves, "model": model}


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_overlay(results: Dict[str, dict], output_path: str):
    """Single shared axis, grouped bars for all algorithms."""
    # Merge importance frames
    all_params = set()
    for r in results.values():
        all_params.update(r["importance"]["parameter"].tolist())
    rows = []
    for p in all_params:
        row = {"parameter": p, "display": SHORT_NAMES.get(p, p), "locked": p in LOCKED_PARAMETERS}
        for algo, r in results.items():
            sub = r["importance"][r["importance"]["parameter"] == p]
            row[f"{algo}_pct"] = float(sub["importance_pct"].iloc[0]) if len(sub) else 0.0
            row[f"{algo}_std_pct"] = float(sub["importance_std"].iloc[0]) if len(sub) else 0.0
        rows.append(row)
    df = pd.DataFrame(rows)
    # Sort by Bayesian importance desc if present, else first algo
    sort_key = f"{'Bayesian' if 'Bayesian' in results else list(results.keys())[0]}_pct"
    df = df.sort_values(sort_key, ascending=False).reset_index(drop=True)

    algos = list(results.keys())
    n_algos = len(algos)
    n = len(df)
    fig, ax = plt.subplots(figsize=(14, max(6, 0.5 * n)))

    y = np.arange(n)
    bar_h = 0.8 / n_algos

    for i, algo in enumerate(algos):
        offset = (i - (n_algos - 1) / 2) * bar_h
        vals = df[f"{algo}_pct"]
        stds = df[f"{algo}_std_pct"]
        color = ALGO_COLORS.get(algo, "#888888")
        bars = ax.barh(
            y + offset, vals, height=bar_h * 0.95,
            color=color, alpha=0.85, label=algo,
            edgecolor="white", linewidth=0.5,
            xerr=stds, error_kw={"ecolor": "#333", "elinewidth": 0.7, "capsize": 2},
        )
        for bar, locked in zip(bars, df["locked"]):
            if locked:
                bar.set_edgecolor(LOCKED_COLOR)
                bar.set_linewidth(1.4)
                bar.set_hatch("//")
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(val + df[[f"{a}_pct" for a in algos]].values.max() * 0.006,
                        bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}%", va="center", ha="left",
                        fontsize=7, color=color)

    from matplotlib.patches import Patch
    locked_patch = Patch(facecolor="white", edgecolor=LOCKED_COLOR,
                         hatch="//", linewidth=1.4, label="Locked parameter")

    ax.set_yticks(y)
    ax.set_yticklabels(df["display"], fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Importance (% of total)", fontsize=11)
    max_val = df[[f"{a}_pct" for a in algos]].values.max()
    ax.set_xlim(0, max_val * 1.18)
    ax.set_title("Parameter Importance: Bayesian vs PSO vs GA (shared axis, normalized)",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    handles, labels = ax.get_legend_handles_labels()
    handles.append(locked_patch)
    ax.legend(handles=handles, loc="lower right", fontsize=10, framealpha=0.95, ncol=2)
    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] {output_path}")


def plot_side_by_side(results: Dict[str, dict], output_path: str):
    """Three (or N) panels side-by-side, one per algorithm."""
    algos = list(results.keys())
    n = len(algos)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, max(6, 0.5 * 13)), sharey=True)
    if n == 1:
        axes = [axes]

    for ax, algo in zip(axes, algos):
        imp = results[algo]["importance"].copy()
        # Normalize to 100%
        total = imp["importance_mean"].sum()
        if total > 0:
            imp["importance_pct"] = (imp["importance_mean"] / total * 100).round(1)
        imp = imp.sort_values("importance_pct", ascending=True)

        colors = [LOCKED_COLOR if p in LOCKED_PARAMETERS else ALGO_COLORS.get(algo, "#888")
                  for p in imp["parameter"]]
        ax.barh(
            imp["parameter"].map(lambda p: SHORT_NAMES.get(p, p)),
            imp["importance_pct"],
            xerr=imp["importance_std"] * 100 / total if total else 0,
            color=colors, edgecolor="white", linewidth=0.5,
        )
        for i, (_, row) in enumerate(imp.iterrows()):
            ax.text(row["importance_pct"] + 1, i, f"{row['importance_pct']:.1f}%",
                    va="center", fontsize=7, color="#333")
        ax.set_title(f"{algo} (n={len(imp)} params)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Importance (%)", fontsize=10)
        ax.grid(axis="x", alpha=0.3)

    fig.suptitle("Parameter Importance: Per-Algorithm Comparison",
                 fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] {output_path}")


def plot_sensitivity_curves(results: Dict[str, dict], output_path: str):
    """One subplot per parameter, lines for each algorithm."""
    # Union of parameters that have curves
    all_params = set()
    for r in results.values():
        if r["curves"] is not None and not r["curves"].empty:
            all_params.update(r["curves"]["parameter"].unique())
    # Sort by Bayesian importance if available
    if "Bayesian" in results:
        order = results["Bayesian"]["importance"]["parameter"].tolist()
    else:
        order = list(results.values())[0]["importance"]["parameter"].tolist()
    params = [p for p in order if p in all_params]
    if not params:
        return

    n_features = len(params)
    n_cols = 3
    n_rows = int(np.ceil(n_features / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 3.6 * n_rows))
    axes = np.atleast_1d(axes).flatten()

    markers = {"Bayesian": "o", "PSO": "s", "GA": "^"}
    linestyles = {"Bayesian": "-", "PSO": "--", "GA": "-."}

    for i, col in enumerate(params):
        ax = axes[i]
        disp = SHORT_NAMES.get(col, col)
        is_locked = col in LOCKED_PARAMETERS
        for algo, r in results.items():
            curves = r["curves"]
            if curves is None or curves.empty:
                continue
            sub = curves[curves["parameter"] == col]
            if sub.empty:
                continue
            ax.plot(sub["parameter_value"], sub["predicted_error"],
                    linewidth=1.8, color=ALGO_COLORS.get(algo, "#888"),
                    label=algo, alpha=0.85, linestyle=linestyles.get(algo, "-"))
            idx = int(np.argmin(sub["predicted_error"].values))
            ax.scatter(sub["parameter_value"].iloc[idx], sub["predicted_error"].iloc[idx],
                       color=ALGO_COLORS.get(algo, "#888"),
                       s=30, zorder=5, marker=markers.get(algo, "o"))
        title = ("[L] " if is_locked else "") + disp
        ax.set_title(title, fontsize=10, fontweight="bold",
                     color=LOCKED_COLOR if is_locked else "black")
        ax.set_xlabel("Parameter Value", fontsize=8)
        ax.set_ylabel("Predicted Error [deg]", fontsize=8)
        ax.grid(alpha=0.3)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, loc="upper right")

    for j in range(n_features, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Local Sensitivity Curves: Bayesian / PSO / GA",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Three-way sensitivity comparison: Bayesian / PSO / GA")
    parser.add_argument("--workspace-dir", type=str, default="./simulation_workspace")
    parser.add_argument("--pso-batch", type=str, default=None,
                        help="PSO batch_results.csv path (single file)")
    parser.add_argument("--ga-batches", type=str, nargs="+", default=None,
                        help="GA batch_results.csv paths (space-separated)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output dir (default: <workspace>/sensitivity_comparison_3way)")
    parser.add_argument("--algorithms", type=str, nargs="+",
                        default=["Bayesian", "PSO", "GA"],
                        help="Subset of algorithms to compare")
    args = parser.parse_args()

    workspace_dir = os.path.abspath(args.workspace_dir)
    output_dir = os.path.abspath(
        args.output_dir or os.path.join(workspace_dir, "sensitivity_comparison_3way")
    )
    os.makedirs(output_dir, exist_ok=True)

    pso_path = args.pso_batch or os.path.join(workspace_dir, "batch_results_full2", "batch_results.csv")
    ga_paths = args.ga_batches or [
        os.path.join(workspace_dir, "batch_results_ga", "batch_results.csv"),
        os.path.join(workspace_dir, "batch_results_ga_resume", "batch_results.csv"),
    ]

    print("=" * 70)
    print("Three-way Sensitivity Comparison: Bayesian / PSO / GA")
    print("=" * 70)
    print(f"Workspace: {workspace_dir}")
    print(f"PSO:       {pso_path}")
    print(f"GA:        {ga_paths}")
    print(f"Output:    {output_dir}")

    # --- Load data ---
    results: Dict[str, dict] = {}

    if "Bayesian" in args.algorithms:
        df_b = load_bayesian_data(workspace_dir)
        param_cols = get_param_columns(df_b)
        results["Bayesian"] = run_algo("Bayesian", df_b, param_cols, output_dir)

    if "PSO" in args.algorithms:
        df_p = load_best_param_data([pso_path], "PSO")
        param_cols_p = get_param_columns(df_p) if "Bayesian" not in results else [
            c for c in results["Bayesian"]["importance"]["parameter"] if c in df_p.columns
        ]
        results["PSO"] = run_algo("PSO", df_p, param_cols_p, output_dir)

    if "GA" in args.algorithms:
        df_g = load_best_param_data(ga_paths, "GA")
        param_cols_g = get_param_columns(df_g) if "Bayesian" not in results else [
            c for c in results["Bayesian"]["importance"]["parameter"] if c in df_g.columns
        ]
        results["GA"] = run_algo("GA", df_g, param_cols_g, output_dir)

    # Drop any failed
    results = {k: v for k, v in results.items() if v is not None}
    if len(results) < 2:
        print("[ERROR] Need at least 2 valid algorithms to compare.")
        return 1

    # --- Plots ---
    print("\n--- Generating Plots ---")
    plot_overlay(results, os.path.join(output_dir, "three_way_importance_overlay.png"))
    plot_sensitivity_curves(results, os.path.join(output_dir, "three_way_sensitivity_curves.png"))

    # --- Summary table ---
    all_params = set()
    for r in results.values():
        all_params.update(r["importance"]["parameter"].tolist())
    # Sort by Bayesian importance desc if available, else first algo
    ref_algo = "Bayesian" if "Bayesian" in results else list(results.keys())[0]
    ref_imp = results[ref_algo]["importance"].set_index("parameter")
    summary_rows = []
    for param in sorted(all_params,
                        key=lambda x: float(ref_imp["importance_pct"].get(x, 0.0)),
                        reverse=True):
        row = {"parameter": param, "display": SHORT_NAMES.get(param, param), "locked": param in LOCKED_PARAMETERS}
        for algo, r in results.items():
            sub = r["importance"][r["importance"]["parameter"] == param]
            row[f"{algo}_pct"] = float(sub["importance_pct"].iloc[0]) if len(sub) else 0.0
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary_path = os.path.join(output_dir, "three_way_summary.csv")
    summary.to_csv(summary_path, index=False, encoding="utf-8")
    print(f"[Output] {summary_path}")

    # Print summary
    algos = list(results.keys())
    print("\n" + "=" * 70)
    print("Three-way Analysis Complete!")
    print("=" * 70)
    hdr = f"{'Parameter':<22}" + "".join(f"{a+'%':>14}" for a in algos)
    print(hdr)
    print("-" * 70)
    for _, row in summary.iterrows():
        cells = "".join(f"{row.get(f'{a}_pct', 0):>13.1f}%" for a in algos)
        print(f"{row['display']:<22}{cells}")

    print(f"\nAll outputs: {output_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
