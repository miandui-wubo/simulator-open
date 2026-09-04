"""
Direct COMSOL simulation interface.

Generates MATLAB .m files from parameters (no LAMMPS, no LLM)
and runs COMSOL via MATLAB subprocess.
"""

import os
import subprocess
import textwrap
import socket
import re
import time
import shutil
from typing import Dict, Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'comsol_work'))
from tools.const_config import matlab_code1, matlab_code2
from simulator.config import LLMCodegenConfig
from simulator.llm_codegen import (
    generate_template_with_local_model,
    validate_generated_template,
)


def _safe_console_text(text: str) -> str:
    """Best-effort conversion to avoid console encoding crashes on Windows."""
    if not text:
        return text
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def _decode_subprocess_bytes(raw: bytes) -> str:
    """Decode subprocess bytes with UTF-8 first, then common Windows fallbacks."""
    if not raw:
        return ""
    for enc in ("utf-8", "gbk", "cp936"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _write_run_debug_log(
    work_dir: str,
    run_id: int,
    phase: str,
    stdout_text: str = "",
    stderr_text: str = "",
    extra: str = "",
) -> str:
    """Persist full MATLAB output for failed runs; console logs only keep tails."""
    debug_dir = os.path.join(work_dir, "debug_logs")
    os.makedirs(debug_dir, exist_ok=True)
    debug_path = os.path.join(debug_dir, f"run_{run_id}_{phase}.log")
    with open(debug_path, "w", encoding="utf-8", errors="replace") as f:
        if extra:
            f.write("=== extra ===\n")
            f.write(extra)
            f.write("\n\n")
        f.write("=== stdout ===\n")
        f.write(stdout_text or "")
        f.write("\n\n=== stderr ===\n")
        f.write(stderr_text or "")
    print(f"[MATLAB] debug log saved: {debug_path}")
    return debug_path


def _read_text_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _is_contact_angle_calculable(txt_path: str) -> tuple[bool, str]:
    """Return whether a generated COMSOL TXT can feed the contact-angle pipeline."""
    if not os.path.exists(txt_path):
        return False, f"TXT does not exist: {txt_path}"

    try:
        import contextlib
        import io
        import math

        from simulator.contact_angle_interface import compute_contact_angle

        # Suppress the calculator's verbose report; the caller only needs validity.
        with contextlib.redirect_stdout(io.StringIO()):
            angle = compute_contact_angle(txt_path, output_dir=None)
        if not math.isfinite(float(angle)):
            return False, f"non-finite contact angle: {angle}"
        return True, f"contact_angle={float(angle):.6f}"
    except Exception as exc:
        return False, str(exc)


def _stabilize_batch_matlab_code(full_code: str) -> str:
    """Disable live plotting in batch mode to avoid Windows Server OpenGL crashes."""
    replacements = {
        "model.study('std1').feature('phasei').set('plot', true);":
            "model.study('std1').feature('phasei').set('plot', false);",
        "model.study('std1').feature('time').set('plot', true);":
            "model.study('std1').feature('time').set('plot', false);",
        "model.sol('sol1').feature('t1').set('plot', true);":
            "model.sol('sol1').feature('t1').set('plot', false);",
    }
    for old, new in replacements.items():
        full_code = full_code.replace(old, new)
    return full_code


PARAMETER_BLOCK_TEMPLATE = textwrap.dedent("""\
    model.component('comp1').material('mat2').label('{{droplet_name}}');
    model.component('comp1').material('mat2').propertyGroup('def').set('dynamicviscosity', '{{droplet_viscosity}}');
    model.component('comp1').material('mat2').propertyGroup('def').set('density', '{{droplet_density}}');
    model.component('comp1').material('mat3').label('{{left_substrate_name}}');
    model.component('comp1').material('mat3').propertyGroup('def').set('thermalconductivity', {'{{left_substrate_thermal_conductivity}}' '0' '0' '0' '{{left_substrate_thermal_conductivity}}' '0' '0' '0' '{{left_substrate_thermal_conductivity}}'});
    model.component('comp1').material('mat3').propertyGroup('def').set('density', '{{left_substrate_density}}');
    model.component('comp1').material('mat3').propertyGroup('def').set('heatcapacity', '{{left_substrate_heat_capacity}}');
    model.component('comp1').material('mat4').label('{{right_substrate_name}}');
    model.component('comp1').material('mat4').propertyGroup('def').set('heatcapacity', '{{right_substrate_heat_capacity}}');
    model.component('comp1').material('mat4').propertyGroup('def').set('density', '{{right_substrate_density}}');
    model.component('comp1').material('mat4').propertyGroup('def').set('thermalconductivity', {'{{right_substrate_thermal_conductivity}}' '0' '0' '0' '{{right_substrate_thermal_conductivity}}' '0' '0' '0' '{{right_substrate_thermal_conductivity}}'});
    model.component('comp1').physics('spf2').prop('PhysicalModelProperty').set('IncludeGravity', true);
    model.component('comp1').physics('ls').feature('init1').set('FluidInDomain', 'Fluid2phils');
    model.component('comp1').physics('ht').feature('init1').set('Tinit', '{{left_substrate_temperature}}[K]');
    model.component('comp1').physics('ht').feature('init1').label([native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ' left']);
    model.component('comp1').physics('ht').feature('init2').set('Tinit', '{{right_substrate_temperature}}[K]');
    model.component('comp1').physics('ht').feature('init2').label([native2unicode(hex2dec({'52' '1d'}), 'unicode')  native2unicode(hex2dec({'59' 'cb'}), 'unicode')  native2unicode(hex2dec({'50' '3c'}), 'unicode') ' right']);
    model.component('comp1').multiphysics('tpf2').set('Fluid1', 'mat2');
    model.component('comp1').multiphysics('tpf2').set('Fluid2', 'mat1');
    model.component('comp1').multiphysics('tpf2').set('IncludeSurfaceTension', true);
    model.component('comp1').multiphysics('tpf2').set('SurfaceTensionCoefficient', 'userdef');
    model.component('comp1').multiphysics('tpf2').set('sigma', '{{surface_tension}}[N/m]');
    model.component('comp1').multiphysics('ww1').set('thetaw', '{{left_contact_angle}}[deg]');
    model.component('comp1').multiphysics('ww2').set('thetaw', '{{right_contact_angle}}[deg]');
""")


def _resolve_placeholder_values(
    params: Dict[str, float],
    material_names: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    names = material_names or {}
    return {
        "droplet_name": str(names.get("droplet_name", "Droplet")),
        "left_substrate_name": str(names.get("left_substrate_name", "LeftSubstrate")),
        "right_substrate_name": str(names.get("right_substrate_name", "RightSubstrate")),
        "droplet_density": str(params.get("droplet_density", 6095)),
        "droplet_viscosity": str(params.get("droplet_viscosity", 0.00181)),
        "left_substrate_density": str(params.get("left_substrate_density", 2329)),
        "left_substrate_heat_capacity": str(params.get("left_substrate_heat_capacity", 700)),
        "left_substrate_thermal_conductivity": str(params.get("left_substrate_thermal_conductivity", 130)),
        "right_substrate_density": str(params.get("right_substrate_density", 6150)),
        "right_substrate_heat_capacity": str(params.get("right_substrate_heat_capacity", 492)),
        "right_substrate_thermal_conductivity": str(params.get("right_substrate_thermal_conductivity", 180)),
        "left_substrate_temperature": str(params.get("left_substrate_temperature", 303.15)),
        "right_substrate_temperature": str(params.get("right_substrate_temperature", 383.15)),
        "surface_tension": str(params.get("surface_tension", 0.35)),
        "left_contact_angle": str(params.get("left_contact_angle", 27.27)),
        "right_contact_angle": str(params.get("right_contact_angle", 13.43)),
    }


def _render_parameter_template(template: str, values: Dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    unresolved = re.findall(r"\{\{[a-zA-Z0-9_]+\}\}", rendered)
    if unresolved:
        raise RuntimeError(
            f"Parameter template has unresolved placeholders: {', '.join(sorted(set(unresolved)))}"
        )
    return rendered


def _get_or_generate_template(
    llm_cfg: LLMCodegenConfig,
    material_names: Optional[Dict[str, str]] = None,
) -> str:
    cache_path = os.path.abspath(llm_cfg.cache_path)
    failed_marker = f"{cache_path}.failed"
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_template = f.read()
        missing = validate_generated_template(cached_template)
        if not missing:
            return cached_template
        print(
            "[LLM] Cached template is invalid (missing placeholders), "
            "fallback to deterministic template."
        )
        return PARAMETER_BLOCK_TEMPLATE
    if os.path.exists(failed_marker):
        with open(failed_marker, "r", encoding="utf-8") as f:
            reason = f.read().strip()
        if "missing placeholders" in reason.lower():
            print(
                "[LLM] Previous template generation failed due to missing placeholders, "
                "fallback to deterministic template."
            )
            return PARAMETER_BLOCK_TEMPLATE
        raise RuntimeError(f"LLM template generation previously failed: {reason}")

    try:
        model_output = generate_template_with_local_model(
            model_dir=llm_cfg.model_dir,
            prompt_path=llm_cfg.prompt_path,
            material_names=material_names,
            timeout_seconds=llm_cfg.timeout_seconds,
        )
        missing = validate_generated_template(model_output)
        if missing:
            raise RuntimeError(f"LLM output missing placeholders: {', '.join(missing)}")
    except Exception as exc:
        if "missing placeholders" in str(exc).lower():
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(failed_marker, "w", encoding="utf-8") as f:
                f.write(str(exc))
            print(
                "[LLM] Generated template misses required placeholders, "
                "fallback to deterministic template."
            )
            return PARAMETER_BLOCK_TEMPLATE
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(failed_marker, "w", encoding="utf-8") as f:
            f.write(str(exc))
        raise

    if os.path.exists(failed_marker):
        os.remove(failed_marker)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(model_output)
    print(f"[LLM] Generated and cached parameter template at: {cache_path}")
    return model_output


def _find_free_tcp_port(host: str = "127.0.0.1") -> int:
    """Ask the OS for an available local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _wait_for_process_start(process: subprocess.Popen, timeout_seconds: float = 5.0) -> bool:
    """Give COMSOL a short startup window without opening a client connection."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        time.sleep(0.5)
    return process.poll() is None


def _kill_process_tree(process: Optional[subprocess.Popen], timeout_seconds: float = 10.0) -> None:
    """Terminate a process and its children; COMSOL often leaves Java children behind."""
    if not process:
        return
    if process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.terminate()

    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass


def _env_flag(name: str, default: bool = True) -> bool:
    """Parse a boolean environment variable with common truthy/falsey values."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _cleanup_stale_comsol_servers() -> None:
    """Best-effort cleanup for orphan COMSOL mphserver processes.

    Why: COMSOL mphserver is single-client by default; if an old client session
    survives abnormally, new mphstart calls can fail with
    'Server is in use by another client'. This cleanup runs under global lock.
    """
    if not _env_flag("SIMULATOR_COMSOL_SWEEP_STALE", default=True):
        return

    image_names = ["comsolmphserver.exe"] if os.name == "nt" else ["comsolmphserver"]
    cleaned_any = False
    for image_name in image_names:
        if os.name == "nt":
            proc = subprocess.run(
                ["taskkill", "/IM", image_name, "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            cleaned = proc.returncode == 0
        else:
            proc = subprocess.run(
                ["pkill", "-f", image_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            cleaned = proc.returncode == 0
        if cleaned:
            cleaned_any = True
            print(f"[COMSOL CLEANUP] Killed stale process image: {image_name}")

    if cleaned_any:
        # Give OS/COMSOL a short grace window to release handles/licenses.
        time.sleep(1.0)


def _stop_server_process(
    server_process: Optional[subprocess.Popen],
    server_port: Optional[int] = None,
) -> None:
    """Best-effort COMSOL server shutdown without touching the COMSOL port."""
    _ = server_port
    _kill_process_tree(server_process)


def _get_default_comsol_lock_path() -> str:
    """Return a cross-process lock path shared by all simulator workers."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(repo_root, "simulation_workspace", ".comsol_global_lock")


def _acquire_comsol_global_lock(wait_timeout_seconds: int = 7200) -> str:
    """Acquire a filesystem-based global COMSOL lock (works across processes)."""
    lock_path = os.environ.get("SIMULATOR_COMSOL_LOCK_PATH", "").strip() or _get_default_comsol_lock_path()
    lock_parent = os.path.dirname(lock_path)
    if lock_parent:
        os.makedirs(lock_parent, exist_ok=True)

    owner_file = os.path.join(lock_path, "owner.txt")
    deadline = time.time() + max(wait_timeout_seconds, 1)
    while True:
        try:
            os.mkdir(lock_path)
            with open(owner_file, "w", encoding="utf-8") as f:
                f.write(f"pid={os.getpid()}\n")
                f.write(f"acquired_at={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            print(f"[COMSOL LOCK] Acquired global lock: {lock_path}")
            return lock_path
        except FileExistsError:
            # Recover from stale lock left by crashed process.
            try:
                lock_age_seconds = time.time() - os.path.getmtime(lock_path)
                if lock_age_seconds > 4 * 3600:
                    shutil.rmtree(lock_path, ignore_errors=True)
                    continue
            except OSError:
                pass
            if time.time() >= deadline:
                owner = _read_text_file(owner_file)
                raise RuntimeError(
                    "等待 COMSOL 全局锁超时，可能存在长时间占用。"
                    f" lock_path={lock_path}; owner={owner.strip() or 'unknown'}"
                )
            time.sleep(2)


def _release_comsol_global_lock(lock_path: Optional[str]) -> None:
    """Release a filesystem-based COMSOL lock."""
    if not lock_path:
        return
    try:
        shutil.rmtree(lock_path, ignore_errors=False)
        print(f"[COMSOL LOCK] Released global lock: {lock_path}")
    except FileNotFoundError:
        pass
    except Exception as exc:
        print(f"[COMSOL LOCK] Failed to release lock {lock_path}: {exc}")


def generate_matlab_parameter_code(params: Dict[str, float],
                                   material_names: Optional[Dict[str, str]] = None,
                                   llm_cfg: Optional[LLMCodegenConfig] = None) -> str:
    """
    Generate the MATLAB code block that sets material properties, physics,
    and multiphysics parameters in the COMSOL model.

    This replaces the LLM-based FEM_model_infer with a deterministic template.

    Args:
        params: dictionary with keys matching the 13 simulation parameters.
        material_names: optional dict with keys droplet_name, left_substrate_name,
                        right_substrate_name.

    Returns:
        A string of MATLAB code to be inserted between matlab_code1 and matlab_code2.
    """
    values = _resolve_placeholder_values(params, material_names)
    if llm_cfg and llm_cfg.enabled:
        try:
            template = _get_or_generate_template(llm_cfg=llm_cfg, material_names=material_names)
            return _render_parameter_template(template, values)
        except Exception as exc:
            if not llm_cfg.allow_fallback_template:
                raise
            print(f"[LLM] Failed to use local model template, fallback to deterministic template: {exc}")

    return _render_parameter_template(PARAMETER_BLOCK_TEMPLATE, values)


def build_full_matlab_script(params: Dict[str, float],
                             output_txt_path: str,
                             material_names: Optional[Dict[str, str]] = None,
                             llm_cfg: Optional[LLMCodegenConfig] = None) -> str:
    """
    Build the complete MATLAB .m script for a COMSOL simulation.

    Returns the full script content as a string.
    """
    param_code = generate_matlab_parameter_code(params, material_names, llm_cfg=llm_cfg)
    full_code = matlab_code1 + "\n" + param_code + "\n" + matlab_code2
    full_code = _stabilize_batch_matlab_code(full_code)
    # 将路径转换为 MATLAB 格式（使用正斜杠）
    matlab_path = output_txt_path.replace("\\", "/")
    full_code = full_code.replace("xxxxxxxxxxxx", matlab_path)
    return full_code


def build_core_m_script(comsol_bin_dir: str, comsol_mli_dir: str,
                        matlab_script_name: str, server_port: int) -> str:
    """Build the core.m startup script that connects to COMSOL server and runs the model."""
    return textwrap.dedent(f"""\
        Currentdir=pwd;
        cd('{comsol_mli_dir}');
        % MATLAB performs the readiness wait. Do not pre-probe the COMSOL TCP
        % port from Python, because COMSOL treats that probe as a client.
        connected=false;
        lastError=[];
        for attempt=1:90
            try
                mphstart({server_port});
                connected=true;
                break;
            catch ME
                lastError=ME;
                fprintf('mphstart attempt %d failed: %s\\n', attempt, ME.message);
                pause(2);
            end
        end
        if ~connected
            rethrow(lastError);
        end
        cd(Currentdir);
        run("{matlab_script_name}.m");
        % 注意：COMSOL server 由 Python 管理，不在此处关闭
    """)


def build_core_m_script_legacy(
    comsol_bin_dir: str,
    comsol_mli_dir: str,
    comsol_server_exe: str,
    matlab_script_name: str,
    server_port: int,
) -> str:
    """Legacy startup flow used in older working scripts.

    Kept for compatibility: legacy MATLAB launch style, but server is still
    managed by Python so process lifecycle is fully controllable.
    """
    comsol_mli_mat = comsol_mli_dir.replace("\\", "/")
    return textwrap.dedent(f"""\
        Currentdir=pwd;
        cd('{comsol_mli_mat}');
        connected=false;
        lastError=[];
        for attempt=1:90
            try
                mphstart({server_port});
                connected=true;
                break;
            catch ME
                lastError=ME;
                fprintf('mphstart attempt %d failed: %s\\n', attempt, ME.message);
                pause(2);
            end
        end
        if ~connected
            rethrow(lastError);
        end
        cd(Currentdir);
        run("{matlab_script_name}.m");
    """)


def run_comsol_simulation(params: Dict[str, float],
                          work_dir: str,
                          comsol_bin_dir: str,
                          comsol_mli_dir: str,
                          material_names: Optional[Dict[str, str]] = None,
                          llm_cfg: Optional[LLMCodegenConfig] = None,
                          run_id: int = 0,
                          timeout_seconds: int = 7200) -> str:
    """
    Run a complete COMSOL simulation.

    1. Generate the MATLAB model script
    2. Generate the core.m launcher
    3. Execute MATLAB
    4. Return the path to the output TXT file

    Args:
        params: simulation parameters
        work_dir: working directory for MATLAB files
        comsol_bin_dir: path to COMSOL bin directory
        comsol_mli_dir: path to COMSOL MLI directory
        material_names: material name overrides
        run_id: integer to disambiguate file names across runs

    Returns:
        Path to the simulation output TXT file.
    """
    lock_path: Optional[str] = None
    work_dir = os.path.abspath(work_dir)
    os.makedirs(work_dir, exist_ok=True)
    txt_dir = os.path.join(work_dir, "txtresult")
    os.makedirs(txt_dir, exist_ok=True)
    temp_dir = os.path.join(work_dir, "_temp")
    os.makedirs(temp_dir, exist_ok=True)

    output_txt = os.path.join(txt_dir, f"simulation_result{run_id}.txt")
    # 使用绝对路径避免工作目录问题
    output_txt_abs = os.path.abspath(output_txt)
    if os.path.exists(output_txt_abs):
        os.remove(output_txt_abs)
    script_name = f"matlabcode{run_id}"

    m_code = build_full_matlab_script(params, output_txt_abs, material_names, llm_cfg=llm_cfg)
    m_path = os.path.join(work_dir, f"{script_name}.m")
    with open(m_path, "w", encoding="utf-8") as f:
        f.write(m_code)

    server_port = _find_free_tcp_port()
    core_code = build_core_m_script(comsol_bin_dir, comsol_mli_dir, script_name, server_port)
    core_path = os.path.join(work_dir, "core.m")
    with open(core_path, "w", encoding="utf-8") as f:
        f.write(core_code)

    # 设置 MATLAB 环境变量，添加 COMSOL paths
    env = os.environ.copy()
    comsol_bin_dir = os.path.abspath(comsol_bin_dir)
    comsol_mli_dir = os.path.abspath(comsol_mli_dir)
    comsol_root = os.path.dirname(os.path.dirname(comsol_bin_dir))  # 移除 /bin/win64
    mli_path = os.path.join(comsol_root, "mli")
    
    # 添加 COMSOL MLI 路径到系统PATH
    env['PATH'] = f'{mli_path};{mli_path}\\matlab;{env.get("PATH", "")}'
    # Force subprocess temp files onto the simulation work disk (typically E:).
    env["TMP"] = temp_dir
    env["TEMP"] = temp_dir
    env["TMPDIR"] = temp_dir
    # COMSOL/Java temporary files should also land in work_dir disk.
    env["COMSOL_TMPDIR"] = temp_dir
    
    # 先启动 COMSOL server
    comsol_server_exe = os.path.join(comsol_bin_dir, "comsolmphserver.exe")
    server_process = None
    server_port_for_cleanup = server_port
    server_stdout_file = None
    server_stderr_file = None
    try:
        lock_path = _acquire_comsol_global_lock()
        _cleanup_stale_comsol_servers()
        debug_dir = os.path.join(work_dir, "debug_logs")
        os.makedirs(debug_dir, exist_ok=True)
        server_stdout_path = os.path.join(debug_dir, f"run_{run_id}_server.stdout.log")
        server_stderr_path = os.path.join(debug_dir, f"run_{run_id}_server.stderr.log")
        print(f"启动 COMSOL server: {comsol_server_exe}")
        server_stdout_file = open(server_stdout_path, "wb")
        server_stderr_file = open(server_stderr_path, "wb")
        server_process = subprocess.Popen(
            [comsol_server_exe, "-port", str(server_port)],
            stdout=server_stdout_file,
            stderr=server_stderr_file,
            cwd=comsol_bin_dir,
            env=env,
        )
        print(f"等待 COMSOL server 进程稳定，随后由 MATLAB mphstart 重试连接 {server_port} 端口...")
        if not _wait_for_process_start(server_process, timeout_seconds=5):
            server_stdout_file.flush()
            server_stderr_file.flush()
            server_stderr = _read_text_file(server_stderr_path)
            raise RuntimeError(
                f"COMSOL server 启动失败，进程提前退出。"
                + (f" server stderr: {server_stderr[-500:]}" if server_stderr else "")
            )

        # 运行 MATLAB，并确保脚本报错时返回非零退出码
        matlab_work_dir = work_dir.replace("\\", "/")
        batch_expr = (
            f"cd('{matlab_work_dir}'); "
            "try, core, catch ME, disp(getReport(ME,'extended')); exit(1); end; exit(0);"
        )
        cmd = ["matlab", "-softwareopengl", "-batch", batch_expr]
        print(f"启动MATLAB: {' '.join(cmd[:3])} <batch-expression>")
        batch_stdout_path = os.path.join(debug_dir, f"run_{run_id}_batch.stdout.log")
        batch_stderr_path = os.path.join(debug_dir, f"run_{run_id}_batch.stderr.log")
        with open(batch_stdout_path, "wb") as stdout_file, open(batch_stderr_path, "wb") as stderr_file:
            matlab_process = subprocess.Popen(
                cmd,
                stdout=stdout_file,
                stderr=stderr_file,
                env=env,
                cwd=work_dir,
            )
            hb_interval = 60
            start_ts = time.time()
            while True:
                rc = matlab_process.poll()
                if rc is not None:
                    break
                elapsed = int(time.time() - start_ts)
                print(f"[MATLAB] still running... elapsed={elapsed}s")
                if elapsed > timeout_seconds:
                    _kill_process_tree(matlab_process, timeout_seconds=30)
                    stdout_file.flush()
                    stderr_file.flush()
                    stdout_text = _read_text_file(batch_stdout_path)
                    stderr_text = _read_text_file(batch_stderr_path)
                    _write_run_debug_log(
                        work_dir,
                        run_id,
                        "batch_timeout",
                        stdout_text=stdout_text,
                        stderr_text=stderr_text,
                        extra=f"timeout_seconds={timeout_seconds}",
                    )
                    raise subprocess.TimeoutExpired(cmd="matlab -batch", timeout=timeout_seconds)
                time.sleep(hb_interval)
            matlab_process.wait()

        stdout_text = _read_text_file(batch_stdout_path)
        stderr_text = _read_text_file(batch_stderr_path)
        stdout_bytes = stdout_text.encode("utf-8", errors="replace")
        stderr_bytes = stderr_text.encode("utf-8", errors="replace")
        if matlab_process.returncode != 0:
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "batch_nonzero",
                stdout_text=stdout_text,
                stderr_text=stderr_text,
                extra=f"returncode={matlab_process.returncode}",
            )
            joined_msg = f"{stderr_text}\n{stdout_text}".lower()
            is_heap_corruption = (
                matlab_process.returncode == 3221226356
                or "0xc0000374" in joined_msg
                or "heap corruption" in joined_msg
            )
            if is_heap_corruption:
                is_usable, reason = _is_contact_angle_calculable(output_txt_abs)
                if is_usable:
                    print(
                        "[MATLAB] Heap corruption occurred after COMSOL exported a usable TXT; "
                        f"treating run as successful. {reason}; debug日志: {debug_path}"
                    )
                    return output_txt_abs
            raise subprocess.CalledProcessError(
                matlab_process.returncode,
                cmd,
                output=stdout_bytes,
                stderr=stderr_bytes,
            )

        if stdout_text:
            print(f"MATLAB stdout最后500字符: {_safe_console_text(stdout_text[-500:])}")
        if stderr_text:
            print(f"MATLAB stderr: {_safe_console_text(stderr_text)}")

        if not os.path.exists(output_txt_abs):
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "batch_no_txt",
                stdout_text=stdout_text,
                stderr_text=stderr_text,
                extra=f"expected_output={output_txt_abs}",
            )
            raise RuntimeError(
                "MATLAB 执行结束但未生成 COMSOL 输出 TXT 文件。"
                f" 预期路径: {output_txt_abs}; debug日志: {debug_path}"
            )

    except subprocess.TimeoutExpired:
        print(
            "[MATLAB] matlab -batch 超时，切换到 legacy 启动方式重试一次 "
            "(matlab -nodesktop -nosplash + core内启动COMSOL server)。"
        )
        _stop_server_process(server_process, server_port_for_cleanup)
        server_process = None

        legacy_port = _find_free_tcp_port()
        server_port_for_cleanup = legacy_port
        legacy_core_code = build_core_m_script_legacy(
            comsol_bin_dir=comsol_bin_dir,
            comsol_mli_dir=comsol_mli_dir,
            comsol_server_exe=comsol_server_exe,
            matlab_script_name=script_name,
            server_port=legacy_port,
        )
        with open(core_path, "w", encoding="utf-8") as f:
            f.write(legacy_core_code)

        print(f"启动 COMSOL server(legacy): {comsol_server_exe}")
        for stream in (server_stdout_file, server_stderr_file):
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass
        server_stdout_file = open(os.path.join(debug_dir, f"run_{run_id}_legacy_server.stdout.log"), "wb")
        server_stderr_file = open(os.path.join(debug_dir, f"run_{run_id}_legacy_server.stderr.log"), "wb")
        server_process = subprocess.Popen(
            [comsol_server_exe, "-port", str(legacy_port)],
            stdout=server_stdout_file,
            stderr=server_stderr_file,
            cwd=comsol_bin_dir,
            env=env,
        )
        print(f"等待 COMSOL server(legacy) 进程稳定，随后由 MATLAB mphstart 重试连接 {legacy_port} 端口...")
        if not _wait_for_process_start(server_process, timeout_seconds=5):
            raise RuntimeError(f"COMSOL server(legacy) 进程提前退出，端口 {legacy_port}。")

        legacy_expr = (
            f"cd('{matlab_work_dir}'); "
            "try, core, catch ME, disp(getReport(ME,'extended')); exit(1); end; exit(0);"
        )
        legacy_cmd = ["matlab", "-softwareopengl", "-batch", legacy_expr]
        legacy_proc = subprocess.run(
            legacy_cmd,
            cwd=work_dir,
            env=env,
            capture_output=True,
            text=False,
            timeout=timeout_seconds,
        )
        if legacy_proc.returncode != 0:
            legacy_stderr = _decode_subprocess_bytes(legacy_proc.stderr or b"").strip()
            legacy_stdout = _decode_subprocess_bytes(legacy_proc.stdout or b"")
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "legacy_timeout_nonzero",
                stdout_text=legacy_stdout,
                stderr_text=legacy_stderr,
                extra=f"returncode={legacy_proc.returncode}",
            )
            legacy_joined = f"{legacy_stderr}\n{legacy_stdout}".lower()
            legacy_heap_corruption = (
                legacy_proc.returncode == 3221226356
                or "0xc0000374" in legacy_joined
                or "heap corruption" in legacy_joined
            )
            if legacy_heap_corruption:
                is_usable, reason = _is_contact_angle_calculable(output_txt_abs)
                if is_usable:
                    print(
                        "[MATLAB] Legacy retry hit heap corruption after exporting a usable TXT; "
                        f"treating run as successful. {reason}; debug日志: {debug_path}"
                    )
                    return output_txt_abs
            raise RuntimeError(
                "MATLAB仿真失败（超时后legacy重试） - "
                f"legacy_stderr: {legacy_stderr}, legacy_stdout片段: {legacy_stdout[-400:]}, "
                f"debug日志: {debug_path}"
            )
        if not os.path.exists(output_txt_abs):
            legacy_stdout = _decode_subprocess_bytes(legacy_proc.stdout or b"")
            legacy_stderr = _decode_subprocess_bytes(legacy_proc.stderr or b"")
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "legacy_timeout_no_txt",
                stdout_text=legacy_stdout,
                stderr_text=legacy_stderr,
                extra=f"expected_output={output_txt_abs}",
            )
            raise RuntimeError(
                "MATLAB legacy 超时重试执行结束但未生成 COMSOL 输出 TXT 文件。"
                f" 预期路径: {output_txt_abs}; debug日志: {debug_path}"
            )
        print("[MATLAB] legacy 启动方式（超时后）重试成功。")

    except subprocess.CalledProcessError as e:
        error_msg = _decode_subprocess_bytes(e.stderr) if e.stderr else "未知错误"
        stdout_msg = _decode_subprocess_bytes(e.stdout) if e.stdout else "无输出"
        joined_msg = f"{error_msg}\n{stdout_msg}".lower()
        is_heap_corruption = (
            e.returncode == 3221226356
            or "0xc0000374" in joined_msg
            or "heap corruption" in joined_msg
        )
        is_access_violation = (
            e.returncode in (3221225477, -1073741819)
            or "0xc0000005" in joined_msg
            or "access violation" in joined_msg
        )
        is_server_busy = "server is in use by another client" in joined_msg
        is_retriable = is_heap_corruption or is_access_violation or is_server_busy
        if not is_retriable:
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "batch_nonretriable",
                stdout_text=stdout_msg,
                stderr_text=error_msg,
                extra=f"returncode={e.returncode}",
            )
            raise RuntimeError(
                f"MATLAB仿真失败 - stderr: {error_msg}, stdout片段: {stdout_msg[-200:]}, "
                f"debug日志: {debug_path}"
            )

        print(
            "[MATLAB] 检测到可重试错误（Access violation/Heap corruption/Server busy），切换到 legacy 启动方式重试一次 "
            "(matlab -nodesktop -nosplash + core内启动COMSOL server)。"
        )
        _stop_server_process(server_process, server_port_for_cleanup)
        server_process = None

        legacy_port = _find_free_tcp_port()
        server_port_for_cleanup = legacy_port
        legacy_core_code = build_core_m_script_legacy(
            comsol_bin_dir=comsol_bin_dir,
            comsol_mli_dir=comsol_mli_dir,
            comsol_server_exe=comsol_server_exe,
            matlab_script_name=script_name,
            server_port=legacy_port,
        )
        with open(core_path, "w", encoding="utf-8") as f:
            f.write(legacy_core_code)

        print(f"启动 COMSOL server(legacy): {comsol_server_exe}")
        for stream in (server_stdout_file, server_stderr_file):
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass
        server_stdout_file = open(os.path.join(debug_dir, f"run_{run_id}_legacy_server.stdout.log"), "wb")
        server_stderr_file = open(os.path.join(debug_dir, f"run_{run_id}_legacy_server.stderr.log"), "wb")
        server_process = subprocess.Popen(
            [comsol_server_exe, "-port", str(legacy_port)],
            stdout=server_stdout_file,
            stderr=server_stderr_file,
            cwd=comsol_bin_dir,
            env=env,
        )
        print(f"等待 COMSOL server(legacy) 进程稳定，随后由 MATLAB mphstart 重试连接 {legacy_port} 端口...")
        if not _wait_for_process_start(server_process, timeout_seconds=5):
            raise RuntimeError(f"COMSOL server(legacy) 进程提前退出，端口 {legacy_port}。")

        legacy_expr = (
            f"cd('{matlab_work_dir}'); "
            "try, core, catch ME, disp(getReport(ME,'extended')); exit(1); end; exit(0);"
        )
        legacy_cmd = ["matlab", "-softwareopengl", "-batch", legacy_expr]
        legacy_proc = subprocess.run(
            legacy_cmd,
            cwd=work_dir,
            env=env,
            capture_output=True,
            text=False,
            timeout=timeout_seconds,
        )
        if legacy_proc.returncode != 0:
            legacy_stderr = _decode_subprocess_bytes(legacy_proc.stderr or b"").strip()
            legacy_stdout = _decode_subprocess_bytes(legacy_proc.stdout or b"")
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "legacy_retry_nonzero",
                stdout_text=legacy_stdout,
                stderr_text=legacy_stderr,
                extra=f"returncode={legacy_proc.returncode}",
            )
            legacy_joined = f"{legacy_stderr}\n{legacy_stdout}".lower()
            legacy_heap_corruption = (
                legacy_proc.returncode == 3221226356
                or "0xc0000374" in legacy_joined
                or "heap corruption" in legacy_joined
            )
            if legacy_heap_corruption:
                is_usable, reason = _is_contact_angle_calculable(output_txt_abs)
                if is_usable:
                    print(
                        "[MATLAB] Legacy retry hit heap corruption after exporting a usable TXT; "
                        f"treating run as successful. {reason}; debug日志: {debug_path}"
                    )
                    return output_txt_abs
            raise RuntimeError(
                "MATLAB仿真失败（含legacy重试） - "
                f"legacy_stderr: {legacy_stderr}, legacy_stdout片段: {legacy_stdout[-400:]}, "
                f"debug日志: {debug_path}"
            )
        if not os.path.exists(output_txt_abs):
            legacy_stdout = _decode_subprocess_bytes(legacy_proc.stdout or b"")
            legacy_stderr = _decode_subprocess_bytes(legacy_proc.stderr or b"")
            debug_path = _write_run_debug_log(
                work_dir,
                run_id,
                "legacy_retry_no_txt",
                stdout_text=legacy_stdout,
                stderr_text=legacy_stderr,
                extra=f"expected_output={output_txt_abs}",
            )
            raise RuntimeError(
                "MATLAB legacy 重试执行结束但未生成 COMSOL 输出 TXT 文件。"
                f" 预期路径: {output_txt_abs}; debug日志: {debug_path}"
            )
        print("[MATLAB] legacy 启动方式重试成功。")
    finally:
        # 关闭 COMSOL server
        if server_process:
            print("关闭 COMSOL server...")
        _stop_server_process(server_process, server_port_for_cleanup)
        for stream in (server_stdout_file, server_stderr_file):
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass
        _release_comsol_global_lock(lock_path)

    return output_txt_abs
