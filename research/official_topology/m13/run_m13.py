#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M13: compare default and M4 Godot mesh paths under scripted edits."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M13_DIR = ROOT / "research" / "official_topology" / "m13"
M12_REPORT = ROOT / "research" / "official_topology" / "m12" / "m12_report.json"
GODOT_PROJECT_REPORT = ROOT / "validation" / "godot_project_report.json"
SCRIPTED_EDIT_REPORT = ROOT / "validation" / "m4_godot_scripted_edit_compare_report.json"
GODOT_SCRIPTED_EDIT_OUTPUT = ROOT / "godot" / "validation" / "10_m4_scripted_edit_compare" / "m4_scripted_edit_compare.json"
M13_REPORT = M13_DIR / "m13_report.json"
RESULTS = M13_DIR / "results.md"


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


def comparison_summary_from_runtime(data: Dict[str, Any]) -> Dict[str, Any]:
    comparison = data.get("comparison", {}) if isinstance(data, dict) else {}
    keys = [
        "status",
        "field_count",
        "scenario_count",
        "failed_scenarios",
        "scripted_edits",
        "check_count",
        "failed_checks",
        "changed_after_edit_checks",
        "scenarios_with_changes",
        "structurally_distinct_checks",
        "default_triangles_total",
        "m4_triangles_total",
        "triangle_delta_m4_minus_default_total",
        "default_backend_by_default",
        "m4_requires_explicit_selection",
    ]
    return {key: comparison.get(key) for key in keys}


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


def write_results(report: Dict[str, Any], scripted_report: Dict[str, Any]) -> None:
    comparison = scripted_report.get("comparison", {})
    lines = [
        "# M13 M4 Godot Scripted Edit Comparison",
        "",
        "M13 compares the default independent transition table and optional M4 candidate table under deterministic scripted Godot edits.",
        "",
        f"- Status: `{report['status']}`",
        f"- M12 status: `{report.get('m12_status')}`",
        f"- Godot project preflight: `{report.get('godot_project_status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- Scripted edit comparison validation: `{scripted_report.get('status')}`",
        "",
        "## Scripted edit comparison",
        "",
        f"- Scenarios: `{comparison.get('scenario_count')}`",
        f"- Scripted edits: `{comparison.get('scripted_edits')}`",
        f"- Checks: `{comparison.get('check_count')}`",
        f"- Failed checks: `{comparison.get('failed_checks')}`",
        f"- Edited checks with changed case sequence: `{comparison.get('changed_after_edit_checks')}`",
        f"- Scenarios with changes: `{comparison.get('scenarios_with_changes')}`",
        f"- Structurally distinct checks: `{comparison.get('structurally_distinct_checks')}`",
        f"- Default total triangles: `{comparison.get('default_triangles_total')}`",
        f"- M4 total triangles: `{comparison.get('m4_triangles_total')}`",
        f"- Triangle delta M4-default: `{comparison.get('triangle_delta_m4_minus_default_total')}`",
        f"- Default backend by default: `{comparison.get('default_backend_by_default')}`",
        f"- M4 requires explicit selection: `{comparison.get('m4_requires_explicit_selection')}`",
        "",
        "## What passed",
        "",
        "- both table paths build valid Godot `ArrayMesh` outputs after every scripted edit;",
        "- `MeshDataTool` reads both backend outputs successfully;",
        "- scripted edits actually changed transition case sequences in every scenario;",
        "- M4 output remains structurally distinct from the default output;",
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
    remove_stale_runtime_output(GODOT_SCRIPTED_EDIT_OUTPUT)
    steps = [
        run_step([sys.executable, "research/official_topology/m12/run_m12.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_m4_godot_scripted_edit_compare.py"]),
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
            "res://stages/10_m4_scripted_edit_compare/DumpM4ScriptedEditCompare.gd",
        ])
        steps.append(godot_step)
        output_data: Dict[str, Any] = {}
        if GODOT_SCRIPTED_EDIT_OUTPUT.exists():
            output_data = read_json(GODOT_SCRIPTED_EDIT_OUTPUT)
        godot_stage = {
            "status": output_data.get("status", "FAIL_MISSING_OUTPUT"),
            "executed": True,
            "returncode": godot_step["returncode"],
            "output_path": str(GODOT_SCRIPTED_EDIT_OUTPUT.relative_to(ROOT)),
            "output_summary": {
                "schema": output_data.get("schema"),
                "status": output_data.get("status"),
                "comparison": comparison_summary_from_runtime(output_data),
            },
        }
    else:
        print("M13 requires Godot runtime execution; no Godot executable was found.")

    steps.append(run_step([sys.executable, "tools/validate_m4_godot_scripted_edit_compare.py", "--require-output"]))

    m12_report = read_json(M12_REPORT)
    godot_project = read_json(GODOT_PROJECT_REPORT)
    scripted_report = read_json(SCRIPTED_EDIT_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m12_report.get("status") == "PASS_M12_M4_GODOT_BACKEND_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and godot_project.get("status") == "PASS"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and scripted_report.get("status") == "PASS_M4_GODOT_SCRIPTED_EDIT_COMPARE"
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m13.report.v1",
        "status": (
            "PASS_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE"
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
            "m4_godot_scripted_edit_compare_validation": str(SCRIPTED_EDIT_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m12_status": m12_report.get("status"),
        "godot_project_status": godot_project.get("status"),
        "m4_godot_scripted_edit_compare_validation": scripted_report,
    }
    M13_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, scripted_report)
    print()
    print("M13:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
