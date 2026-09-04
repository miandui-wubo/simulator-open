#!/usr/bin/env python3
"""
Combine Bayesian and PSO importance on a single shared coordinate system.

Reads importance_bayesian.csv and importance_pso.csv (both already normalized
to 100% as importance_pct) and produces a single grouped horizontal bar chart
where each parameter has two adjacent bars (Bayesian vs PSO).

Usage:
    python -m simulator.sensitivity_overlay
"""

from __future__ import annotations

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

LOCKED_PARAMETERS = {
    "left_substrate_temperature",
    "right_substrate_temperature",
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

# Color palette matching the original comparison
BAYES_COLOR = "#1f77b4"   # blue
PSO_COLOR = "#ff7f0e"     # orange
LOCKED_FILL = "#d62728"   # red (used as edge color to mark locked params)


def load_pair(bayes_csv: str, pso_csv: str) -> pd.DataFrame:
    b = pd.read_csv(bayes_csv).set_index("parameter")
    p = pd.read_csv(pso_csv).set_index("parameter")
    all_params = sorted(set(b.index) | set(p.index))
    rows = []
    for param in all_params:
        b_pct = float(b.loc[param, "importance_pct"]) if param in b.index else 0.0
        b_std = float(b.loc[param, "importance_std"]) if param in b.index else 0.0
        p_pct = float(p.loc[param, "importance_pct"]) if param in p.index else 0.0
        p_std = float(p.loc[param, "importance_std"]) if param in p.index else 0.0
        rows.append({
            "parameter": param,
            "display": SHORT_NAMES.get(param, param),
            "locked": param in LOCKED_PARAMETERS,
            "bayes_pct": b_pct,
            "bayes_std_pct": b_std,
            "pso_pct": p_pct,
            "pso_std_pct": p_std,
        })
    df = pd.DataFrame(rows)
    # Sort by Bayesian importance descending so most important params are at top
    df = df.sort_values("bayes_pct", ascending=False).reset_index(drop=True)
    return df


def plot_overlay(df: pd.DataFrame, output_path: str) -> str:
    n = len(df)
    fig, ax = plt.subplots(figsize=(12, max(6, 0.45 * n)))

    y = np.arange(n)
    bar_h = 0.38

    # Bayesian bar (offset up)
    b_bars = ax.barh(
        y - bar_h / 2, df["bayes_pct"], height=bar_h,
        color=BAYES_COLOR, alpha=0.85, label="Bayesian",
        edgecolor="white", linewidth=0.5,
        xerr=df["bayes_std_pct"], error_kw={"ecolor": "#333", "elinewidth": 0.8, "capsize": 2},
    )
    # PSO bar (offset down)
    p_bars = ax.barh(
        y + bar_h / 2, df["pso_pct"], height=bar_h,
        color=PSO_COLOR, alpha=0.85, label="PSO",
        edgecolor="white", linewidth=0.5,
        xerr=df["pso_std_pct"], error_kw={"ecolor": "#333", "elinewidth": 0.8, "capsize": 2},
    )

    # Mark locked parameters with red edges + hatch
    for bar, locked in zip(b_bars, df["locked"]):
        if locked:
            bar.set_edgecolor(LOCKED_FILL)
            bar.set_linewidth(1.6)
            bar.set_hatch("//")
    for bar, locked in zip(p_bars, df["locked"]):
        if locked:
            bar.set_edgecolor(LOCKED_FILL)
            bar.set_linewidth(1.6)
            bar.set_hatch("//")

    # Annotate values
    max_val = max(df["bayes_pct"].max(), df["pso_pct"].max())
    for bar, val in zip(b_bars, df["bayes_pct"]):
        if val > 0:
            ax.text(val + max_val * 0.008, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", ha="left",
                    fontsize=8, color=BAYES_COLOR)
    for bar, val in zip(p_bars, df["pso_pct"]):
        if val > 0:
            ax.text(val + max_val * 0.008, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", ha="left",
                    fontsize=8, color=PSO_COLOR)

    # Locked legend entry (proxy artist)
    from matplotlib.patches import Patch
    locked_patch = Patch(facecolor="white", edgecolor=LOCKED_FILL,
                         hatch="//", linewidth=1.4, label="Locked parameter")

    ax.set_yticks(y)
    ax.set_yticklabels(df["display"], fontsize=10)
    ax.invert_yaxis()  # top = most important
    ax.set_xlabel("Importance (% of total)", fontsize=11)
    ax.set_xlim(0, max_val * 1.18)
    ax.set_title("Parameter Importance: Bayesian vs PSO (shared axis, normalized)",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    # Combined legend
    handles, labels = ax.get_legend_handles_labels()
    handles.append(locked_patch)
    ax.legend(handles=handles, loc="lower right", fontsize=10, framealpha=0.95)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[Output] {output_path}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Overlay Bayesian + PSO importance on shared axis")
    parser.add_argument("--workspace-dir", type=str, default="./simulation_workspace",
                        help="Workspace root containing sensitivity_comparison/")
    parser.add_argument("--output", type=str, default=None,
                        help="Output PNG path (default: sensitivity_comparison/combined_importance.png)")
    args = parser.parse_args()

    sens_dir = os.path.join(os.path.abspath(args.workspace_dir), "sensitivity_comparison")
    bayes_csv = os.path.join(sens_dir, "importance_bayesian.csv")
    pso_csv = os.path.join(sens_dir, "importance_pso.csv")

    for p in (bayes_csv, pso_csv):
        if not os.path.exists(p):
            print(f"[ERROR] Missing input: {p}")
            return 1

    output_path = args.output or os.path.join(sens_dir, "combined_importance.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df = load_pair(bayes_csv, pso_csv)
    print(f"Loaded {len(df)} parameters")
    print(df[["display", "bayes_pct", "pso_pct"]].to_string(index=False))
    plot_overlay(df, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
