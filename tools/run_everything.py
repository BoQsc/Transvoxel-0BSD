#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run modes for the Transvoxel 0BSD package.

Modes:
  full        - full release proof: Python proof + C core + dist + Godot dumps + production gate.
  fast        - everyday proof: Python proof + dist only. Does not claim production gate.
  core        - engine-independent C core compile/dist proof only.
  godot       - Godot runtime/mesh/seam dumps + production gate only.
  interactive - open the staged Godot interactive sandbox for human evaluation.
  auto        - run deterministic scripted auto-interaction proof in Godot headless.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
PROOF_DIR = ROOT / "proof"
LOG_PATH = PROOF_DIR / "one_click_log.txt"
REPORT_PATH = PROOF_DIR / "one_click_report.json"
SUMMARY_PATH = PROOF_DIR / "ONE_CLICK_RESULT.txt"
RUNS_DIR = ROOT / "runs"
BUNDLE_PATH = PROOF_DIR / "SEND_TO_CHATGPT.zip"


def now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def session_status() -> Dict[str, Any]:
    path = ROOT / "godot" / "validation" / "06_interactive_sandbox" / "session.json"
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "exists": False, "status": "NOT_RUN"}
    data = read_json(path)
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "exists": True,
        "status": str(data.get("status", "UNKNOWN")),
        "field_mode": data.get("field_mode"),
        "edit_count": data.get("edit_count"),
        "dig_count": data.get("dig_count"),
        "add_count": data.get("add_count"),
        "seam_open_edges": data.get("seam_open_edges"),
        "invalid_triangles": data.get("invalid_triangles"),
        "degenerate_triangles": data.get("degenerate_triangles"),
    }


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def append_log(text: str) -> None:
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(text)


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def archive_run_outputs(run_id: str) -> Optional[Path]:
    if not run_id:
        return None
    dst = RUNS_DIR / run_id
    dst.mkdir(parents=True, exist_ok=True)
    for rel in [
        "proof/ONE_CLICK_RESULT.txt",
        "proof/one_click_log.txt",
        "proof/one_click_report.json",
        "proof/production_gate.json",
        "proof/proof_dump.json",
        "proof/tables",
        "validation",
        "godot/validation",
        "dist/transvoxel_0bsd_core.zip",
    ]:
        copy_if_exists(ROOT / rel, dst / rel)
    (dst / "RUN_ID.txt").write_text(run_id + "\n", encoding="utf-8")
    return dst


def add_file_to_zip(zf: zipfile.ZipFile, src: Path, arc: str) -> None:
    if src.exists() and src.is_file():
        zf.write(src, arc)


def add_dir_to_zip(zf: zipfile.ZipFile, src: Path, arc_root: str) -> None:
    if not src.exists() or not src.is_dir():
        return
    for path in sorted(src.rglob("*")):
        if path.is_file():
            zf.write(path, str(Path(arc_root) / path.relative_to(src)))


def create_upload_bundle(run_id: str, archive_dir: Optional[Path]) -> Optional[Path]:
    try:
        PROOF_DIR.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "boqsc.transvoxel.chatgpt_upload_bundle.v4",
            "run_id": run_id,
            "purpose": "Single file to upload for debugging or confirming a Transvoxel 0BSD run.",
            "notes": [
                "Contains run logs, reports, gate status, Godot validation dumps when present, and failure diagnostics if present.",
                "Does not include full generated table JSON files unless they appear inside a report.",
                "If RUN_INTERACTIVE.cmd was used and the sandbox wrote session.json, that session is included too.",
            ],
        }
        manifest_path = PROOF_DIR / "upload_bundle_manifest.json"
        write_json(manifest_path, manifest)
        with zipfile.ZipFile(BUNDLE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            add_file_to_zip(zf, manifest_path, "upload_bundle_manifest.json")
            for rel in [
                "VERSION",
                "proof/ONE_CLICK_RESULT.txt",
                "proof/one_click_log.txt",
                "proof/one_click_report.json",
                "proof/production_gate.json",
                "proof/proof_dump.json",
                "validation/proof_report.json",
                "validation/proof_report.md",
                "validation/all_tables_report.json",
                "validation/boundary_report.json",
                "validation/neighbor_report.json",
                "validation/chunk_report.json",
                "validation/transvoxel_report.json",
                "validation/validation_report.json",
                "validation/godot_project_report.json",
                "validation/m4_godot_candidate_report.json",
                "validation/m4_godot_viewer_report.json",
                "validation/m4_godot_backend_compare_report.json",
                "validation/m4_godot_scripted_edit_compare_report.json",
                "validation/m4_six_face_orientation_report.json",
                "validation/m4_replacement_readiness_report.json",
                "validation/m4_replacement_readiness_report.md",
                "validation/core_c_report.json",
                "validation/m4_backend_c_report.json",
                "validation/m4_terrain_c_report.json",
                "validation/dist_report.json",
                "godot/validation/01_runtime/runtime_dump.json",
                "godot/validation/02_mesh_api/mesh_api_dump.json",
                "godot/validation/03_seam_metrics/seam_metrics.json",
                "godot/validation/05_m4_candidate_metrics/m4_candidate_metrics.json",
                "godot/validation/06_interactive_sandbox/session.json",
                "godot/validation/07_auto_interaction/auto_interaction.json",
                "godot/validation/08_m4_candidate_viewer/m4_candidate_viewer.json",
                "godot/validation/09_m4_backend_compare/m4_backend_compare.json",
                "godot/validation/10_m4_scripted_edit_compare/m4_scripted_edit_compare.json",
                "godot/validation/11_m4_six_face_orientation/m4_six_face_orientation.json",
                "validation/auto_interaction_report.json",
                "validation/external_alignment_report.json",
                "validation/topology_signature_report.json",
                "validation/topology_signature_report.md",
                "validation/official_equivalence_research_report.json",
                "validation/topology_comparison_no_copy_report.json",
        "validation/official_73_candidate_derivation.json",
        "validation/reference_convention_matrix.json",
        "validation/official_topology_constraints.json",
                "validation/strict_correctness_audit.json",
                "validation/strict_correctness_audit.md",
                "validation/official_73_candidate_derivation.json",
                "validation/official_73_candidate_derivation.md",
                "validation/reference_convention_matrix.json",
                "validation/official_topology_constraints.json",
                "validation/project_tracks_report.json",
                "validation/release_candidate_report.json",
                "validation/equivalence_class_report.json",
                "validation/winding_normals_report.json",
                "validation/self_intersection_report.json",
                "validation/reference_convention_report.json",
                "validation/corner_junction_report.json",
            ]:
                add_file_to_zip(zf, ROOT / rel, rel)
            add_dir_to_zip(zf, ROOT / "validation" / "failure_obj", "validation/failure_obj")
            if archive_dir is not None:
                add_file_to_zip(zf, archive_dir / "RUN_ID.txt", "run_archive/RUN_ID.txt")
        if archive_dir is not None:
            shutil.copy2(BUNDLE_PATH, archive_dir / "SEND_TO_CHATGPT.zip")
        return BUNDLE_PATH
    except Exception as exc:
        append_log("upload bundle creation failed: " + repr(exc) + "\n")
        return None


def display_cmd(cmd: List[str]) -> str:
    parts: List[str] = []
    for p in cmd:
        if " " in p or "\t" in p:
            parts.append('"' + p.replace('"', '\\"') + '"')
        else:
            parts.append(p)
    return " ".join(parts)


def run_cmd(name: str, cmd: List[str], cwd: Path, allow_nonzero: bool = False) -> Dict[str, Any]:
    print("\n==", name, "==")
    print(display_cmd(cmd))
    append_log("\n== " + name + " ==\n" + display_cmd(cmd) + "\n")
    start = _dt.datetime.now()
    try:
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    except Exception as exc:
        msg = "START FAILED: " + repr(exc)
        print(msg)
        append_log(msg + "\n")
        return {"name": name, "cmd": cmd, "ok": False, "returncode": None, "error": repr(exc), "elapsed_seconds": 0.0}
    output_lines: List[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
        output_lines.append(line)
        append_log(line)
    rc = proc.wait()
    elapsed = (_dt.datetime.now() - start).total_seconds()
    ok = (rc == 0) or allow_nonzero
    print(f"[{name}] rc={rc} elapsed={elapsed:.2f}s")
    append_log(f"[{name}] rc={rc} elapsed={elapsed:.2f}s\n")
    return {"name": name, "cmd": cmd, "ok": ok, "returncode": rc, "elapsed_seconds": round(elapsed, 3), "output_tail": "".join(output_lines[-60:])}


def candidate_paths_from_file() -> List[Path]:
    out: List[Path] = []
    for name in ["godot_path.txt", "GODOT_PATH.txt"]:
        path_file = ROOT / name
        if path_file.exists():
            raw = path_file.read_text(encoding="utf-8", errors="replace").strip().strip('"')
            if raw:
                out.append(Path(raw))
    return out


def find_godot() -> Optional[Path]:
    env = os.environ.get("GODOT_EXE", "").strip().strip('"')
    candidates: List[Path] = []
    if env:
        candidates.append(Path(env))
    candidates.extend(candidate_paths_from_file())
    for name in ["godot", "godot.exe", "Godot", "Godot.exe"]:
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    if platform.system().lower().startswith("win"):
        common_roots: List[Path] = []
        for env_name in ["ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA", "USERPROFILE"]:
            value = os.environ.get(env_name)
            if value:
                common_roots.append(Path(value))
        steam_roots = []
        for base in common_roots:
            steam_roots.append(base / "Steam" / "steamapps" / "common" / "Godot Engine")
            steam_roots.append(base / "steamapps" / "common" / "Godot Engine")
            steam_roots.append(base / "Programs" / "Godot")
            steam_roots.append(base / "Godot")
        for base in steam_roots:
            if base.exists():
                try:
                    for exe in sorted(base.rglob("*.exe")):
                        n = exe.name.lower()
                        if "godot" in n and "crash" not in n and "handler" not in n:
                            candidates.append(exe)
                except Exception:
                    pass
    else:
        for p in [Path("/usr/bin/godot"), Path("/usr/local/bin/godot"), Path("/opt/godot/godot")]:
            candidates.append(p)
    seen = set()
    for c in candidates:
        try:
            c = c.expanduser().resolve()
        except Exception:
            c = c.expanduser()
        key = str(c).lower()
        if key in seen:
            continue
        seen.add(key)
        if c.exists() and c.is_file():
            return c
    return None


def write_not_run_gate(mode: str) -> Dict[str, Any]:
    gate = {
        "schema": "boqsc.transvoxel.production_gate.v1",
        "status": "NOT_RUN",
        "mode": mode,
        "meaning": "This run mode intentionally did not run the production gate. Use RUN_FULL.cmd for release proof.",
        "missing_data_files": [],
        "missing_or_failed_reports": [],
        "seam_reasons": [],
    }
    write_json(PROOF_DIR / "production_gate.json", gate)
    return gate


def make_summary(report: Dict[str, Any]) -> str:
    gate = report.get("production_gate", {}) or {}
    lines = [
        "Transvoxel 0BSD run result",
        "===========================",
        "time: " + str(report.get("time")),
        "mode: " + str(report.get("mode")),
        "status: " + str(report.get("status")),
        "production_gate: " + str(gate.get("status", "missing")),
        "",
        "Godot executable: " + str(report.get("godot_exe") or "not found / skipped"),
        "",
    ]
    if report.get("mode") != "full":
        lines.append("This was not the full release proof. Use RUN_FULL.cmd for the full production gate.")
        lines.append("")
    missing = gate.get("missing_data_files") or []
    if missing:
        lines.append("Missing production-gate data:")
        for item in missing:
            lines.append("  - " + str(item))
        lines.append("")
    seam_reasons = gate.get("seam_reasons") or []
    if seam_reasons:
        lines.append("Seam reasons:")
        for item in seam_reasons:
            lines.append("  - " + str(item))
        lines.append("")
    lines.append("Reports present in this run:")
    for rel in [
        "proof/SEND_TO_CHATGPT.zip",
        "proof/one_click_report.json",
        "proof/one_click_log.txt",
        "proof/production_gate.json",
        "validation/proof_report.json",
        "validation/core_c_report.json",
        "validation/m4_backend_c_report.json",
        "validation/m4_terrain_c_report.json",
        "validation/m4_godot_candidate_report.json",
        "validation/m4_godot_viewer_report.json",
        "validation/m4_godot_backend_compare_report.json",
        "validation/m4_godot_scripted_edit_compare_report.json",
        "validation/m4_six_face_orientation_report.json",
        "validation/m4_replacement_readiness_report.json",
        "validation/m4_replacement_readiness_report.md",
        "validation/dist_report.json",
        "dist/transvoxel_0bsd_core.zip",
        "godot/validation/01_runtime/runtime_dump.json",
        "godot/validation/02_mesh_api/mesh_api_dump.json",
        "godot/validation/03_seam_metrics/seam_metrics.json",
        "godot/validation/05_m4_candidate_metrics/m4_candidate_metrics.json",
        "godot/validation/06_interactive_sandbox/session.json",
        "godot/validation/07_auto_interaction/auto_interaction.json",
        "godot/validation/08_m4_candidate_viewer/m4_candidate_viewer.json",
        "godot/validation/09_m4_backend_compare/m4_backend_compare.json",
        "godot/validation/10_m4_scripted_edit_compare/m4_scripted_edit_compare.json",
        "godot/validation/11_m4_six_face_orientation/m4_six_face_orientation.json",
        "validation/auto_interaction_report.json",
        "validation/external_alignment_report.json",
        "validation/official_equivalence_research_report.json",
        "validation/topology_comparison_no_copy_report.json",
        "validation/official_73_candidate_derivation.json",
        "validation/reference_convention_matrix.json",
        "validation/official_topology_constraints.json",
    ]:
        if (ROOT / rel).exists():
            lines.append("  - " + rel)
    sess = report.get("interactive_session") or {}
    if sess:
        lines.append("")
        lines.append("interactive_session: " + str(sess.get("status")))
        lines.append("interactive_session_file: " + str(sess.get("path")))
    return "\n".join(lines) + "\n"


def run_python_proof(steps: List[Dict[str, Any]], py: str) -> bool:
    steps.append(run_cmd("python proof suite", [py, "tools/prove_tables.py"], ROOT))
    return bool(steps[-1]["ok"])


def run_core(steps: List[Dict[str, Any]], py: str) -> bool:
    ok = True
    steps.append(run_cmd("core C smoke test", [py, "tools/test_core_c.py"], ROOT))
    ok = ok and bool(steps[-1]["ok"])
    steps.append(run_cmd("M4 backend package C test", [py, "tools/test_m4_backend_c.py"], ROOT))
    ok = ok and bool(steps[-1]["ok"])
    steps.append(run_cmd("M4 terrain export C test", [py, "tools/test_m4_terrain_c.py"], ROOT))
    ok = ok and bool(steps[-1]["ok"])
    steps.append(run_cmd("build core dist", [py, "tools/build_dist.py"], ROOT))
    ok = ok and bool(steps[-1]["ok"])
    return ok


def run_dist_only(steps: List[Dict[str, Any]], py: str) -> bool:
    steps.append(run_cmd("build core dist", [py, "tools/build_dist.py"], ROOT))
    return bool(steps[-1]["ok"])


def run_godot_steps(steps: List[Dict[str, Any]], py: str, godot_exe: Path, include_gate: bool = True, include_auto: bool = True) -> bool:
    hard_ok = True
    print("\nGodot executable:", godot_exe)
    godot_dir = ROOT / "godot"
    for name, script in [
        ("godot runtime dump", "res://stages/01_runtime/DumpRuntimeData.gd"),
        ("godot mesh api dump", "res://stages/02_mesh_api/DumpMeshData.gd"),
        ("godot seam metrics", "res://stages/03_seam_metrics/DumpSeamMetrics.gd"),
        ("godot M4 candidate metrics", "res://stages/05_m4_candidate_metrics/DumpM4CandidateMetrics.gd"),
        ("godot M4 candidate viewer", "res://stages/08_m4_candidate_viewer/DumpM4CandidateViewer.gd"),
        ("godot M4 backend compare", "res://stages/09_m4_backend_compare/DumpM4BackendCompare.gd"),
        ("godot M4 scripted edit compare", "res://stages/10_m4_scripted_edit_compare/DumpM4ScriptedEditCompare.gd"),
        ("godot M4 six-face orientation", "res://stages/11_m4_six_face_orientation/DumpM4SixFaceOrientation.gd"),
    ]:
        steps.append(run_cmd(name, [str(godot_exe), "--headless", "--path", str(godot_dir), "--script", script], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok and include_auto:
        steps.append(run_cmd("godot auto interaction", [str(godot_exe), "--headless", "--path", str(godot_dir), "--script", "res://stages/07_auto_interaction/DumpAutoInteraction.gd"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok:
        steps.append(run_cmd("validate godot dump", [py, "tools/validate_godot_dump.py"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok:
        steps.append(run_cmd("validate M4 Godot viewer", [py, "tools/validate_m4_godot_viewer.py", "--require-output"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok:
        steps.append(run_cmd("validate M4 Godot backend compare", [py, "tools/validate_m4_godot_backend_compare.py", "--require-output"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok:
        steps.append(run_cmd("validate M4 Godot scripted edit compare", [py, "tools/validate_m4_godot_scripted_edit_compare.py", "--require-output"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok:
        steps.append(run_cmd("validate M4 six-face orientation", [py, "tools/validate_m4_six_face_orientation.py", "--require-output"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if hard_ok and include_auto:
        steps.append(run_cmd("validate auto interaction", [py, "tools/validate_auto_interaction.py"], ROOT))
        hard_ok = hard_ok and bool(steps[-1]["ok"])
    if include_gate:
        steps.append(run_cmd("check production gate", [py, "tools/check_production_gate.py"], ROOT, allow_nonzero=True))
    return hard_ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "fast", "core", "godot", "interactive", "auto"], default="full", help="Run mode. full is release proof; fast skips slow C/Godot steps.")
    parser.add_argument("--godot", help="Path to Godot executable. Overrides auto-detection and GODOT_EXE.")
    parser.add_argument("--skip-godot", action="store_true", help="Only for --mode full: run full non-Godot steps but skip Godot headless dumps.")
    parser.add_argument("--strict-gate", action="store_true", help="Return nonzero when production gate is not PASS.")
    parser.add_argument("--pause", action="store_true", help="Wait for Enter before exiting.")
    args = parser.parse_args()

    run_id = "run_" + _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("Transvoxel 0BSD run log\nstarted=" + now() + "\nmode=" + args.mode + "\n", encoding="utf-8")

    steps: List[Dict[str, Any]] = []
    py = sys.executable
    hard_failure = False
    gate: Dict[str, Any] = {}
    gate_status = "NOT_RUN"
    godot_exe: Optional[Path] = None

    if args.mode == "fast":
        hard_failure = not run_python_proof(steps, py)
        hard_failure = (not run_dist_only(steps, py)) or hard_failure
        gate = write_not_run_gate("fast")
        status = "FAST_PASS" if not hard_failure else "FAIL"

    elif args.mode == "core":
        hard_failure = not run_core(steps, py)
        gate = write_not_run_gate("core")
        status = "CORE_PASS" if not hard_failure else "FAIL"

    elif args.mode == "godot":
        if args.godot:
            godot_exe = Path(args.godot.strip().strip('"'))
        else:
            godot_exe = find_godot()
        if godot_exe is None or not godot_exe.exists():
            print("\nGodot executable not found.")
            append_log("\nGodot executable not found.\n")
            hard_failure = True
        else:
            hard_failure = not run_godot_steps(steps, py, godot_exe, include_gate=True)
        gate = read_json(PROOF_DIR / "production_gate.json")
        gate_status = str(gate.get("status", "UNKNOWN")).upper()
        if hard_failure:
            status = "FAIL"
        elif gate_status == "PASS":
            status = "GODOT_PASS"
        else:
            status = "BLOCKED_BY_PRODUCTION_GATE"

    elif args.mode == "auto":
        if args.godot:
            godot_exe = Path(args.godot.strip().strip('\"'))
        else:
            godot_exe = find_godot()
        if godot_exe is None or not godot_exe.exists():
            print("\nGodot executable not found.")
            append_log("\nGodot executable not found.\n")
            hard_failure = True
            gate = write_not_run_gate("auto")
            status = "FAIL"
        else:
            godot_dir = ROOT / "godot"
            steps.append(run_cmd("godot seam metrics precheck", [str(godot_exe), "--headless", "--path", str(godot_dir), "--script", "res://stages/03_seam_metrics/DumpSeamMetrics.gd"], ROOT))
            hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
            if not hard_failure:
                steps.append(run_cmd("godot auto interaction", [str(godot_exe), "--headless", "--path", str(godot_dir), "--script", "res://stages/07_auto_interaction/DumpAutoInteraction.gd"], ROOT))
                hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
            if not hard_failure:
                steps.append(run_cmd("validate auto interaction", [py, "tools/validate_auto_interaction.py"], ROOT))
                hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
            gate = write_not_run_gate("auto")
            status = "AUTO_PASS" if not hard_failure else "FAIL"

    elif args.mode == "interactive":
        if args.godot:
            godot_exe = Path(args.godot.strip().strip('\"'))
        else:
            godot_exe = find_godot()
        if godot_exe is None or not godot_exe.exists():
            print("\nGodot executable not found.")
            append_log("\nGodot executable not found.\n")
            hard_failure = True
            status = "FAIL"
        else:
            godot_dir = ROOT / "godot"
            seam_script = "res://stages/03_seam_metrics/DumpSeamMetrics.gd"
            # Keep interactive sessions self-contained: write the reference seam metrics first,
            # but do not turn personal evaluation into the full production gate.
            steps.append(run_cmd("godot seam metrics precheck", [str(godot_exe), "--headless", "--path", str(godot_dir), "--script", seam_script], ROOT, allow_nonzero=True))
            scene_path = "res://stages/06_interactive_sandbox/InteractiveSandbox.tscn"
            steps.append(run_cmd("godot interactive sandbox", [str(godot_exe), "--path", str(godot_dir), scene_path], ROOT))
            hard_failure = not bool(steps[-1]["ok"])
            status = "INTERACTIVE_DONE" if not hard_failure else "FAIL"
        gate = write_not_run_gate("interactive")

    else:  # full
        hard_failure = not run_python_proof(steps, py)
        hard_failure = (not run_core(steps, py)) or hard_failure
        if args.godot:
            godot_exe = Path(args.godot.strip().strip('"'))
        elif not args.skip_godot:
            godot_exe = find_godot()
        if args.skip_godot:
            print("\nGodot step skipped by --skip-godot")
            append_log("\nGodot step skipped by --skip-godot\n")
        elif godot_exe is None or not godot_exe.exists():
            print("\nGodot executable not found.")
            print("Set GODOT_EXE, pass --godot, or write the path into godot_path.txt.")
            append_log("\nGodot executable not found.\n")
            hard_failure = True
        else:
            hard_failure = (not run_godot_steps(steps, py, godot_exe, include_gate=False)) or hard_failure
        if not args.skip_godot and not hard_failure:
            # The Python proof suite runs strict_correctness_audit before Godot runtime
            # data exists. Rerun it here so corner/seam/auto-interaction evidence is
            # reflected in the final uploaded reports.
            steps.append(run_cmd("post-godot strict correctness audit", [py, "tools/strict_correctness_audit.py"], ROOT))
            hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
        if not args.skip_godot and not hard_failure:
            steps.append(run_cmd("check production gate", [py, "tools/check_production_gate.py"], ROOT, allow_nonzero=True))
        elif args.skip_godot:
            gate = write_not_run_gate("full_skip_godot")
        if not args.skip_godot and not hard_failure:
            # The Python proof suite also runs external_alignment_report before
            # Godot auto-interaction and the final production gate exist. Rerun
            # it last so the uploaded report reflects the complete full run.
            steps.append(run_cmd("post-gate external alignment report", [py, "tools/external_alignment_report.py"], ROOT))
            hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
        if not args.skip_godot and not hard_failure:
            steps.append(run_cmd("post-gate official equivalence research", [py, "tools/official_equivalence_research.py"], ROOT))
            hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
        if not args.skip_godot and not hard_failure:
            steps.append(run_cmd("post-gate topology comparison no-copy", [py, "tools/topology_comparison_no_copy.py"], ROOT))
            hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
        if not args.skip_godot and not hard_failure:
            steps.append(run_cmd("post-gate project tracks report", [py, "tools/project_tracks_report.py"], ROOT))
            hard_failure = (not bool(steps[-1]["ok"])) or hard_failure
        if not gate:
            gate = read_json(PROOF_DIR / "production_gate.json")
        gate_status = str(gate.get("status", "UNKNOWN")).upper()
        if hard_failure:
            status = "FAIL"
        elif gate_status == "PASS":
            status = "PASS"
        else:
            status = "BLOCKED_BY_PRODUCTION_GATE"

    if not gate:
        gate = read_json(PROOF_DIR / "production_gate.json")
        gate_status = str(gate.get("status", "UNKNOWN")).upper()

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.one_click_report.v4",
        "time": now(),
        "run_id": run_id,
        "mode": args.mode,
        "status": status,
        "root": str(ROOT),
        "python": sys.executable,
        "platform": platform.platform(),
        "godot_exe": str(godot_exe) if godot_exe else None,
        "steps": steps,
        "production_gate": gate,
        "interactive_session": session_status(),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    summary = make_summary(report)
    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    archive_dir = archive_run_outputs(run_id)
    bundle = create_upload_bundle(run_id, archive_dir)
    if archive_dir is not None:
        report["run_archive"] = str(archive_dir)
    if bundle is not None:
        report["upload_bundle"] = str(bundle)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    if archive_dir is not None:
        summary += "\nArchived run snapshot:\n  - " + str(archive_dir.relative_to(ROOT)).replace("\\", "/") + "\n"
    if bundle is not None:
        summary += "\nSingle file to upload here:\n  - " + str(bundle.relative_to(ROOT)).replace("\\", "/") + "\n"
    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    print("\n" + summary)

    if args.pause:
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass

    if hard_failure:
        return 1
    if args.strict_gate and gate_status != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
