"""
Local checkpoint based code generation helpers.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional


REQUIRED_MODEL_FILES = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
)

PLACEHOLDERS = (
    "{{droplet_name}}",
    "{{left_substrate_name}}",
    "{{right_substrate_name}}",
    "{{droplet_viscosity}}",
    "{{droplet_density}}",
    "{{left_substrate_density}}",
    "{{left_substrate_heat_capacity}}",
    "{{left_substrate_thermal_conductivity}}",
    "{{right_substrate_density}}",
    "{{right_substrate_heat_capacity}}",
    "{{right_substrate_thermal_conductivity}}",
    "{{left_substrate_temperature}}",
    "{{right_substrate_temperature}}",
    "{{surface_tension}}",
    "{{left_contact_angle}}",
    "{{right_contact_angle}}",
)


def find_weight_files(model_dir: str) -> List[str]:
    model_dir = os.path.abspath(model_dir)
    patterns = ("*.safetensors", "*.bin", "*.pt")
    files: List[str] = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(model_dir, pattern)))
    for idx_name in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        idx_path = os.path.join(model_dir, idx_name)
        if os.path.exists(idx_path):
            files.append(idx_path)
    return sorted(set(files))


def validate_local_checkpoint(model_dir: str) -> Dict[str, object]:
    model_dir = os.path.abspath(model_dir)
    if not os.path.isdir(model_dir):
        return {"ok": False, "reason": f"Model directory does not exist: {model_dir}"}

    missing = [name for name in REQUIRED_MODEL_FILES if not os.path.exists(os.path.join(model_dir, name))]
    if missing:
        return {"ok": False, "reason": f"Checkpoint missing required files: {', '.join(missing)}"}

    weight_files = find_weight_files(model_dir)
    if not weight_files:
        return {
            "ok": False,
            "reason": (
                "No model weight files found (*.safetensors/*.bin/*.pt). "
                "Please place checkpoint weights into the model directory."
            ),
        }

    return {"ok": True, "reason": "Checkpoint files look complete.", "weights": weight_files}


def _read_prompt_text(prompt_path: str) -> str:
    prompt_path = os.path.abspath(prompt_path)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_template_request(material_names: Optional[Dict[str, str]] = None) -> str:
    names = material_names or {}
    sample = {
        "Droplet_Name": names.get("droplet_name", "Ga"),
        "Left_Substrate_Material_Name": names.get("left_substrate_name", "Si"),
        "Right_Substrate_Material_Name": names.get("right_substrate_name", "GaN"),
        "Droplet_Dynamic_Viscosity": "{{droplet_viscosity}}",
        "Droplet_Density": "{{droplet_density}}",
        "Left_Substrate_Density": "{{left_substrate_density}}",
        "Left_Substrate_Heat_Capacity_at_Constant_Pressure": "{{left_substrate_heat_capacity}}",
        "Left_Substrate_Thermal_Conductivity": "{{left_substrate_thermal_conductivity}}",
        "Right_Substrate_Density": "{{right_substrate_density}}",
        "Right_Substrate_Heat_Capacity_at_Constant_Pressure": "{{right_substrate_heat_capacity}}",
        "Right_Substrate_Thermal_Conductivity": "{{right_substrate_thermal_conductivity}}",
        "Left_Substrate_Temperature": "{{left_substrate_temperature}}",
        "Right_Substrate_Temperature": "{{right_substrate_temperature}}",
        "Droplet_Surface_Tension": "{{surface_tension}}",
        "Left_Substrate_Contact_Angle": "{{left_contact_angle}}",
        "Right_Substrate_Contact_Angle": "{{right_contact_angle}}",
        "Output_Format_Requirement": "Only output MATLAB parameter-setting code segment. No markdown.",
        "Strict_Placeholder_Rule": (
            "Do not resolve placeholders. Keep double-curly placeholders exactly as provided."
        ),
    }
    return json.dumps(sample, ensure_ascii=False)


def _swap_file(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    backup = f"{path}.bak"
    if os.path.exists(backup):
        os.remove(backup)
    shutil.move(path, backup)
    return backup


def _restore_file(path: str, backup: Optional[str]) -> None:
    if backup and os.path.exists(backup):
        if os.path.exists(path):
            os.remove(path)
        shutil.move(backup, path)
    elif os.path.exists(path):
        os.remove(path)


def _run_infer_script(model_dir: str, timeout_seconds: int = 600) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            [sys.executable, "matlab_infer.py"],
            cwd=model_dir,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.CalledProcessError as exc:
        stderr_tail = (exc.stderr or "")[-1200:]
        stdout_tail = (exc.stdout or "")[-1200:]
        raise RuntimeError(
            f"matlab_infer.py failed with exit={exc.returncode}; "
            f"stderr_tail={stderr_tail}; stdout_tail={stdout_tail}"
        ) from exc


def _resolve_runner_dir(checkpoint_dir: str) -> str:
    script_name = "matlab_infer.py"
    if os.path.exists(os.path.join(checkpoint_dir, script_name)):
        return checkpoint_dir
    parent_dir = os.path.dirname(checkpoint_dir)
    if os.path.exists(os.path.join(parent_dir, script_name)):
        return parent_dir
    raise FileNotFoundError(
        f"Could not find {script_name} in checkpoint dir or parent dir. "
        f"checkpoint_dir={checkpoint_dir}"
    )


def generate_template_with_local_model(
    model_dir: str,
    prompt_path: str,
    material_names: Optional[Dict[str, str]] = None,
    timeout_seconds: int = 600,
) -> str:
    checkpoint_dir = os.path.abspath(model_dir)
    runner_dir = _resolve_runner_dir(checkpoint_dir)
    prompt_text = _read_prompt_text(prompt_path)
    infer_input = {
        "instruction": prompt_text,
        "input": build_template_request(material_names),
    }
    input_path = os.path.join(runner_dir, "matlab_input.jsonl")
    output_path = os.path.join(runner_dir, "matlab_output.jsonl")

    in_backup = _swap_file(input_path)
    out_backup = _swap_file(output_path)
    try:
        with open(input_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(infer_input, ensure_ascii=False) + "\n")

        _run_infer_script(runner_dir, timeout_seconds=timeout_seconds)

        if not os.path.exists(output_path):
            raise RuntimeError(f"matlab_infer.py finished without output file: {output_path}")

        with open(output_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if not first_line:
            raise RuntimeError("matlab_output.jsonl is empty.")

        payload = json.loads(first_line)
        generated = payload.get("predict", "").strip()
        if not generated:
            raise RuntimeError("Local model returned empty code output.")
        return generated
    finally:
        _restore_file(input_path, in_backup)
        _restore_file(output_path, out_backup)


def validate_generated_template(template_text: str) -> List[str]:
    missing = [token for token in PLACEHOLDERS if token not in template_text]
    return missing


def healthcheck_local_codegen(
    model_dir: str,
    prompt_path: str,
    timeout_seconds: int = 600,
) -> Dict[str, object]:
    chk = validate_local_checkpoint(model_dir)
    if not chk["ok"]:
        return chk

    try:
        generated = generate_template_with_local_model(
            model_dir=model_dir,
            prompt_path=prompt_path,
            material_names=None,
            timeout_seconds=timeout_seconds,
        )
        missing = validate_generated_template(generated)
        if missing:
            return {
                "ok": False,
                "reason": f"Model output missing placeholders: {', '.join(missing)}",
            }
        return {"ok": True, "reason": "Local checkpoint inference succeeded."}
    except Exception as exc:
        return {"ok": False, "reason": f"Inference test failed: {exc}"}
