#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M12: compare default and M4 Godot transition-strip mesh paths."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M12_DIR = ROOT / "research" / "official_topology" / "m12"
M11_REPORT = ROOT / "research" / "official_topology" / "m11" / "m11_report.json"
GODOT_PROJECT_REPORT = ROOT / "validation" / "godot_project_report.json"
BACKEND_COMPARE_REPORT = ROOT / "validation" / "m4_godot_backend_compare_report.json"
GODOT_COMPARE_OUTPUT = ROOT / "godot" / "validation" / "09_m4_backend_compare" / "m4_backend_compare.json"
M12_REPORT = M12_DIR / "m12_report.json"
RESULTS = M12_DIR / "results.md"


def stable_command(command: List[str]) -> List[str]:
    out: List[str] = []
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            out.append("python")
        elif index == 0 and Path(item).name.lower() in ("godot", "godot.exe"):
            out.append("godot")
        else:
            out.append(item.replace(root_native, "<repo>").replace(root_forward, "<repo>"))
    return out


def sanitize_output(output: str) -> str:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    out = output.replace(root_native, "<repo>").replace(root_forward, "<repo>")
    out = out.replace(str(Path(sys.executable)), "python")
    return out


def run_step(command: List[str]) -> Dict[str, object]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    return {
        "command": stable_command(command),
        "returncode": proc.returncode,
        "output": sanitize_output(proc.stdout),
    }


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def remove_stale_runtime_output(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def find_godot() -> Path | None:
    candidates: List[Path] = []
    env = os.environ.get("GODOT_EXE", "").strip().strip('"')
    if env:
        candidates.append(Path(env))
    for name in ["godot_path.txt", "GODOT_PATH.txt"]:
        path_file = ROOT / name
        if path_file.exists():
            raw = path_file.read_text(encoding="utf-8", errors="replace").strip().strip('"')
            if raw:
                candidates.append(Path(raw))
    for name in ["godot", "godot.exe"]:
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    candidates.append(Path("C:/Program Files (x86)/Steam/steamapps/common/Godot Engine/godot.exe"))
    candidates.append(Path("C:/Program Files/Steam/steamapps/common/Godot Engine/godot.exe"))
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            resolved = candidate.expanduser()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists() and resolved.is_file():
            return resolved
    return None


def write_results(report: Dict[str, Any], compare_report: Dict[str, Any]) -> None:
    comparison = compare_report.get("comparison", {})
    default_backend = compare_report.get("default_backend", {})
    m4_backend = compare_report.get("m4_backend", {})
    default_mesh = default_backend.get("mesh", {}) if isinstance(default_backend, dict) else {}
    m4_mesh = m4_backend.get("mesh", {}) if isinstance(m4_backend, dict) else {}
    lines = [
        "# M12 M4 Godot Backend Comparison",
        "",
        "M12 compares the default independent transition table and optional M4 candidate table through the same Godot mesh path.",
        "",
        f"- Status: `{report['status']}`",
        f"- M11 status: `{report.get('m11_status')}`",
        f"- Godot project preflight: `{report.get('godot_project_status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- Backend comparison validation: `{compare_report.get('status')}`",
        "",
        "## Comparison",
        "",
        f"- Same case sequence: `{comparison.get('same_case_sequence')}`",
        f"- Same non-empty cell count: `{comparison.get('same_non_empty_cell_count')}`",
        f"- Default vertices/triangles: `{default_mesh.get('array_vertex_count')}` / `{default_mesh.get('triangle_count')}`",
        f"- M4 vertices/triangles: `{m4_mesh.get('array_vertex_count')}` / `{m4_mesh.get('triangle_count')}`",
        f"- Vertex delta M4-default: `{comparison.get('vertex_delta_m4_minus_default')}`",
        f"- Triangle delta M4-default: `{comparison.get('triangle_delta_m4_minus_default')}`",
        f"- M4 structurally distinct: `{comparison.get('m4_structurally_distinct_from_default')}`",
        f"- Default backend by default: `{comparison.get('default_backend_by_default')}`",
        f"- M4 requires explicit selection: `{comparison.get('m4_requires_explicit_selection')}`",
        "",
        "## What passed",
        "",
        "- both table paths build valid Godot `ArrayMesh` outputs;",
        "- `MeshDataTool` reads both outputs successfully;",
        "- both paths use the same deterministic case sequence;",
        "- M4 output is structurally distinct from the default output;",
        "- M4 remains opt-in and the default backend remains unchanged;",
        "",
        "## What remains unproven",
        "",
        "- official Transvoxel.cpp byte/table identity;",
        "- official class ID mapping;",
        "- official triangle topology equivalence;",
        "- finished gameplay terrain integration through Godot/GDExtension;",
        "- decision to make M4 the default backend.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    remove_stale_runtime_output(GODOT_COMPARE_OUTPUT)
    steps = [
        run_step([sys.executable, "research/official_topology/m11/run_m11.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_m4_godot_backend_compare.py"]),
    ]
    godot = find_godot()
    godot_stage: Dict[str, Any] = {
        "status": "NOT_RUN_GODOT_NOT_FOUND",
        "executed": False,
        "output": None,
    }
    if godot is not None:
        godot_step = run_step([
            str(godot),
            "--headless",
            "--path",
            "godot",
            "--script",
            "res://stages/09_m4_backend_compare/DumpM4BackendCompare.gd",
        ])
        steps.append(godot_step)
        output_data: Dict[str, Any] = {}
        if GODOT_COMPARE_OUTPUT.exists():
            output_data = read_json(GODOT_COMPARE_OUTPUT)
        godot_stage = {
            "status": output_data.get("status", "FAIL_MISSING_OUTPUT"),
            "executed": True,
            "returncode": godot_step["returncode"],
            "output_path": str(GODOT_COMPARE_OUTPUT.relative_to(ROOT)),
            "output": output_data,
        }
    else:
        print("M12 requires Godot runtime execution; no Godot executable was found.")

    steps.append(run_step([sys.executable, "tools/validate_m4_godot_backend_compare.py", "--require-output"]))

    m11_report = read_json(M11_REPORT)
    godot_project = read_json(GODOT_PROJECT_REPORT)
    compare_report = read_json(BACKEND_COMPARE_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m11_report.get("status") == "PASS_M11_M4_GODOT_VIEWER_EXPORT_PATH_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and godot_project.get("status") == "PASS"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and compare_report.get("status") == "PASS_M4_GODOT_BACKEND_COMPARE"
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m12.report.v1",
        "status": (
            "PASS_M12_M4_GODOT_BACKEND_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M12_M4_GODOT_BACKEND_COMPARE"
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "godot_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "steps": steps,
        "outputs": {
            "godot_project_preflight": str(GODOT_PROJECT_REPORT.relative_to(ROOT)),
            "m4_godot_backend_compare_validation": str(BACKEND_COMPARE_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m11_status": m11_report.get("status"),
        "godot_project_status": godot_project.get("status"),
        "m4_godot_backend_compare_validation": compare_report,
    }
    M12_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, compare_report)
    print()
    print("M12:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
