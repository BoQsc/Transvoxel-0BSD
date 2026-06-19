#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M11: M4 candidate through a real Godot viewer/export mesh path."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M11_DIR = ROOT / "research" / "official_topology" / "m11"
M10_REPORT = ROOT / "research" / "official_topology" / "m10" / "m10_report.json"
GODOT_PROJECT_REPORT = ROOT / "validation" / "godot_project_report.json"
M4_VIEWER_REPORT = ROOT / "validation" / "m4_godot_viewer_report.json"
GODOT_VIEWER_OUTPUT = ROOT / "godot" / "validation" / "08_m4_candidate_viewer" / "m4_candidate_viewer.json"
M11_REPORT = M11_DIR / "m11_report.json"
RESULTS = M11_DIR / "results.md"


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


def write_results(report: Dict[str, Any], viewer_report: Dict[str, Any]) -> None:
    gallery = viewer_report.get("case_gallery", {})
    gallery_mesh = gallery.get("mesh", {}) if isinstance(gallery, dict) else {}
    strip = viewer_report.get("terrain_strip", {})
    strip_mesh = strip.get("mesh", {}) if isinstance(strip, dict) else {}
    lines = [
        "# M11 M4 Godot Viewer/Export Path",
        "",
        "M11 validates that the M4 candidate table can feed real Godot mesh creation and readback.",
        "",
        f"- Status: `{report['status']}`",
        f"- M10 status: `{report.get('m10_status')}`",
        f"- Godot project preflight: `{report.get('godot_project_status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- M4 viewer validation: `{viewer_report.get('status')}`",
        "",
        "## Runtime mesh outputs",
        "",
        f"- Case gallery vertices: `{gallery_mesh.get('array_vertex_count')}`",
        f"- Case gallery triangles: `{gallery_mesh.get('triangle_count')}`",
        f"- Case gallery MeshDataTool error: `{gallery_mesh.get('mdt_create_error')}`",
        f"- Terrain strip non-empty cells: `{strip.get('non_empty_cells')}`",
        f"- Terrain strip vertices: `{strip_mesh.get('array_vertex_count')}`",
        f"- Terrain strip triangles: `{strip_mesh.get('triangle_count')}`",
        f"- Terrain strip MeshDataTool error: `{strip_mesh.get('mdt_create_error')}`",
        f"- Invalid triangles: `{strip_mesh.get('invalid_triangles')}`",
        f"- Degenerate triangles: `{strip_mesh.get('degenerate_triangles')}`",
        "",
        "## What passed",
        "",
        "- the M4 candidate table is available in `godot/generated/`;",
        "- the stage builds real `ArrayMesh` objects from M4 candidate cases;",
        "- `MeshDataTool` can read back the generated M4 gallery and strip meshes;",
        "- the deterministic M4 terrain-strip-style mesh has nonzero cells, vertices, and triangles;",
        "- M4 remains optional and the default backend remains unchanged;",
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
    steps = [
        run_step([sys.executable, "research/official_topology/m10/run_m10.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_m4_godot_viewer.py"]),
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
            "res://stages/08_m4_candidate_viewer/DumpM4CandidateViewer.gd",
        ])
        steps.append(godot_step)
        output_data: Dict[str, Any] = {}
        if GODOT_VIEWER_OUTPUT.exists():
            output_data = read_json(GODOT_VIEWER_OUTPUT)
        godot_stage = {
            "status": output_data.get("status", "FAIL_MISSING_OUTPUT"),
            "executed": True,
            "returncode": godot_step["returncode"],
            "output_path": str(GODOT_VIEWER_OUTPUT.relative_to(ROOT)),
            "output": output_data,
        }
    else:
        print("M11 requires Godot runtime execution; no Godot executable was found.")

    steps.append(run_step([sys.executable, "tools/validate_m4_godot_viewer.py", "--require-output"]))

    m10_report = read_json(M10_REPORT)
    godot_project = read_json(GODOT_PROJECT_REPORT)
    viewer_report = read_json(M4_VIEWER_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m10_report.get("status") == "PASS_M10_M4_GODOT_DATA_PATH_METRICS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and godot_project.get("status") == "PASS"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and viewer_report.get("status") == "PASS_M4_GODOT_VIEWER_EXPORT_PATH"
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m11.report.v1",
        "status": (
            "PASS_M11_M4_GODOT_VIEWER_EXPORT_PATH_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M11_M4_GODOT_VIEWER_EXPORT_PATH"
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
            "m4_godot_viewer_validation": str(M4_VIEWER_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m10_status": m10_report.get("status"),
        "godot_project_status": godot_project.get("status"),
        "m4_godot_viewer_validation": viewer_report,
    }
    M11_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, viewer_report)
    print()
    print("M11:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
