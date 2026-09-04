"""
Experiment dataset normalization utilities.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Dict, List


REQUIRED_COLUMNS = (
    "experiment_id",
    "target_left_contact_angle",
    "target_right_contact_angle",
    "left_substrate_temperature_k",
    "right_substrate_temperature_k",
    "droplet_name",
    "left_substrate_name",
    "right_substrate_name",
    "mesh_fineness",
)


def _to_float(row: Dict[str, str], key: str) -> float:
    value = row.get(key)
    if value is None or value == "":
        raise ValueError(f"Missing required numeric field: {key}")
    return float(value)


def _to_int(row: Dict[str, str], key: str) -> int:
    value = row.get(key)
    if value is None or value == "":
        raise ValueError(f"Missing required integer field: {key}")
    return int(float(value))


def normalize_experiment_row(row: Dict[str, str]) -> Dict:
    """
    Convert one CSV row into the runtime schema used by simulator batch mode.
    """
    for col in REQUIRED_COLUMNS:
        if col not in row:
            raise ValueError(f"Required column not found in CSV: {col}")

    normalized = {
        "experiment_id": row["experiment_id"].strip(),
        "target_left_contact_angle": _to_float(row, "target_left_contact_angle"),
        "target_right_contact_angle": _to_float(row, "target_right_contact_angle"),
        "left_substrate_temperature_k": _to_float(row, "left_substrate_temperature_k"),
        "right_substrate_temperature_k": _to_float(row, "right_substrate_temperature_k"),
        "droplet_name": row["droplet_name"].strip(),
        "left_substrate_name": row["left_substrate_name"].strip(),
        "right_substrate_name": row["right_substrate_name"].strip(),
        "mesh_fineness": _to_int(row, "mesh_fineness"),
        "raw": dict(row),
    }
    return normalized


def load_experiments_csv(csv_path: str) -> List[Dict]:
    """
    Load and normalize experiments from CSV.
    """
    csv_path = os.path.abspath(csv_path)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Experiments CSV not found: {csv_path}")

    experiments: List[Dict] = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            experiments.append(normalize_experiment_row(row))

    if not experiments:
        raise ValueError(f"No experiment rows found in: {csv_path}")
    return experiments


def write_runtime_jsonl(experiments: List[Dict], output_path: str) -> None:
    """
    Persist normalized experiments for reproducibility.
    """
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for exp in experiments:
            f.write(json.dumps(exp, ensure_ascii=False) + "\n")
