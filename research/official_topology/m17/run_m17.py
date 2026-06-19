#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M17: M4-selected combined production gate."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M17_DIR = ROOT / "research" / "official_topology" / "m17"
M16_REPORT = ROOT / "research" / "official_topology" / "m16" / "m16_report.json"
C_REPORT = M17_DIR / "m17_c_validation.json"
BACKEND_REPORT = ROOT / "validation" / "m4_backend_c_report.json"
TERRAIN_REPORT = ROOT / "validation" / "m4_terrain_c_report.json"
SCRIPTED_REPORT = ROOT / "validation" / "m4_godot_scripted_edit_compare_report.json"
SCRIPTED_OUTPUT = (
    ROOT
    / "godot"
    / "validation"
    / "10_m4_scripted_edit_compare"
    / "m4_scripted_edit_compare.json"
)
M4_GATE = ROOT / "proof" / "m4_production_gate.json"
READINESS_REPORT = ROOT / "validation" / "m4_replacement_readiness_report.json"
M17_REPORT = M17_DIR / "m17_report.json"
RESULTS = M17_DIR / "results.md"
PASS_STATUS = (
    "PASS_M17_M4_SELECTED_PRODUCTION_GATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
)


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
            out.append(
                item.replace(root_native, "<repo>").replace(root_forward, "<repo>")
            )
    return out


def sanitize_output(output: str) -> str:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    return (
        output.replace(root_native, "<repo>")
        .replace(root_forward, "<repo>")
        .replace(str(Path(sys.executable)), "python")
    )


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
            raw = path_file.read_text(
                encoding="utf-8", errors="replace"
            ).strip().strip('"')
            if raw:
                candidates.append(Path(raw))
    for name in ["godot", "godot.exe"]:
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    candidates.extend([
        Path("C:/Program Files (x86)/Steam/steamapps/common/Godot Engine/godot.exe"),
        Path("C:/Program Files/Steam/steamapps/common/Godot Engine/godot.exe"),
    ])
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


def scripted_comparison_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    comparison = data.get("comparison", {})
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


def write_results(
    report: Dict[str, Any],
    gate: Dict[str, Any],
    readiness: Dict[str, Any],
) -> None:
    metrics = report.get("c_metrics", {})
    lines = [
        "# M17 M4-Selected Production Gate",
        "",
        "M17 combines the normal C backend hook, mapped corner geometry, terrain export, Godot scripted edits, six-face validation, corner junctions, and the base production gate.",
        "",
        f"- Status: `{report['status']}`",
        f"- M16 status: `{report.get('m16_status')}`",
        f"- M4 production gate: `{gate.get('status')}`",
        f"- Godot scripted-edit runtime executed: `{report.get('godot_scripted_runtime_executed')}`",
        "",
        "## Combined C assembler",
        "",
        f"- Normal API cases: `{metrics.get('normal_cases')}`",
        f"- Normal API vertices/triangles: `{metrics.get('normal_vertices')}` / `{metrics.get('normal_triangles')}`",
        f"- Mapped builds: `{metrics.get('mapped_builds')}`",
        f"- Mapped vertices/triangles: `{metrics.get('mapped_vertices')}` / `{metrics.get('mapped_triangles')}`",
        f"- Default backend restored: `{metrics.get('restored_default')}`",
        f"- Failures: `{metrics.get('failures')}`",
        "",
        "## Readiness effect",
        "",
        f"- M4-selected production gate: `{report.get('production_gate_status')}`",
        f"- Ready to replace default transition backend: `{readiness.get('decisions', {}).get('ready_to_replace_default_transition_backend')}`",
        f"- Functional full replacement ready: `{readiness.get('decisions', {}).get('functional_full_replacement_ready')}`",
        f"- Remaining blocking gates: `{len(readiness.get('blocking_gate_ids', []))}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "M17 proves the M4 candidate's default-backend production gate. It does not prove official reference/topology behavior or a full Transvoxel.cpp replacement.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    remove_stale_runtime_output(SCRIPTED_OUTPUT)
    steps = [
        run_step([sys.executable, "research/official_topology/m16/run_m16.py"]),
        run_step([sys.executable, "tools/test_m4_backend_c.py"]),
        run_step([sys.executable, "tools/test_m4_terrain_c.py"]),
        run_step([sys.executable, "research/official_topology/m17/test_m4_production_c.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
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
        if SCRIPTED_OUTPUT.exists():
            output_data = read_json(SCRIPTED_OUTPUT)
        godot_stage = {
            "status": output_data.get("status", "FAIL_MISSING_OUTPUT"),
            "executed": True,
            "returncode": godot_step["returncode"],
            "output_path": str(SCRIPTED_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
            "comparison": scripted_comparison_summary(output_data),
        }
    else:
        print("M17 requires Godot runtime execution; no Godot executable was found.")

    steps.extend([
        run_step([
            sys.executable,
            "tools/validate_m4_godot_scripted_edit_compare.py",
            "--require-output",
        ]),
        run_step([sys.executable, "tools/check_production_gate.py"]),
        run_step([sys.executable, "tools/check_m4_production_gate.py"]),
    ])

    m16 = read_json(M16_REPORT)
    c_report = read_json(C_REPORT)
    backend = read_json(BACKEND_REPORT)
    terrain = read_json(TERRAIN_REPORT)
    scripted = read_json(SCRIPTED_REPORT)
    gate = read_json(M4_GATE)
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and m16.get("status")
        == "PASS_M16_M4_DEFORMED_CORNER_JUNCTIONS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and c_report.get("status")
        == "PASS_M17_ZIG_M4_SELECTED_PRODUCTION_ASSEMBLER"
        and backend.get("status") == "PASS_M4_BACKEND_PACKAGE_C_EXAMPLE"
        and terrain.get("status") == "PASS_M4_TERRAIN_NORMAL_API_EXPORT"
        and scripted.get("status") == "PASS_M4_GODOT_SCRIPTED_EDIT_COMPARE"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and gate.get("status") == "PASS_M4_SELECTED_PRODUCTION_GATE"
    )

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m17.report.v1",
        "status": PASS_STATUS if base_ok else "FAIL_M17_M4_SELECTED_PRODUCTION_GATE",
        "meaning": (
            "M17 passes only when M4 is selected through the normal C backend "
            "hook, mapped geometry runs in the same assembler, current Godot "
            "scripted edits pass, and all prior orientation/junction/base "
            "production gates are green."
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_reference_convention_equivalence": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "m16_status": m16.get("status"),
        "c_status": c_report.get("status"),
        "c_metrics": c_report.get("metrics", {}),
        "backend_status": backend.get("status"),
        "terrain_status": terrain.get("status"),
        "scripted_edit_status": scripted.get("status"),
        "godot_scripted_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "m4_production_gate": gate,
        "steps": steps,
        "outputs": {
            "c_validation": str(C_REPORT.relative_to(ROOT)).replace("\\", "/"),
            "m4_production_gate": str(M4_GATE.relative_to(ROOT)).replace("\\", "/"),
            "results": str(RESULTS.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    M17_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_step = run_step([sys.executable, "tools/m4_replacement_readiness.py"])
    steps.append(readiness_step)
    readiness = read_json(READINESS_REPORT)
    production_gate = next(
        (
            item
            for item in readiness.get("gates", [])
            if item.get("id") == "m4_selected_full_production_gate"
        ),
        {},
    )
    final_ok = (
        base_ok
        and readiness_step["returncode"] == 0
        and readiness.get("status")
        == "READY_M4_DEFAULT_TRANSITION_BACKEND_FUNCTIONAL_FULL_REPLACEMENT_BLOCKED"
        and production_gate.get("status") == "PASS"
        and readiness.get("decisions", {}).get(
            "ready_to_replace_default_transition_backend"
        )
        is True
        and readiness.get("decisions", {}).get(
            "functional_full_replacement_ready"
        )
        is False
        and readiness.get("next_milestone", {}).get("id")
        == "M18_OFFICIAL_REFERENCE_CONVENTION_VALIDATION"
    )
    report["status"] = (
        PASS_STATUS if final_ok else "FAIL_M17_M4_SELECTED_PRODUCTION_GATE"
    )
    report["steps"] = steps
    report["production_gate_status"] = production_gate.get("status")
    report["readiness_status"] = readiness.get("status")
    report["readiness_decisions"] = readiness.get("decisions", {})
    report["next_milestone"] = readiness.get("next_milestone", {})
    M17_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report, gate, readiness)
    print()
    print("M17:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
