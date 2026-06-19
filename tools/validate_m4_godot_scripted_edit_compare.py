#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the optional M4/default Godot scripted-edit comparison report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "godot" / "stages" / "10_m4_scripted_edit_compare" / "DumpM4ScriptedEditCompare.gd"
GODOT_OUTPUT = ROOT / "godot" / "validation" / "10_m4_scripted_edit_compare" / "m4_scripted_edit_compare.json"
REPORT = ROOT / "validation" / "m4_godot_scripted_edit_compare_report.json"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def validate_stage_source() -> List[str]:
    issues: List[str] = []
    if not STAGE.exists():
        return ["missing " + rel(STAGE)]
    text = STAGE.read_text(encoding="utf-8")
    for token in [
        "DEFAULT_PATH",
        "M4_PATH",
        "OUT_PATH",
        "_scripted_edits_for_field",
        "_run_scenario",
        "_run_compare",
        "_make_array_mesh",
        "MeshDataTool",
    ]:
        if token not in text:
            issues.append(f"stage missing token {token}")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and ":=" in stripped:
            issues.append(f"ambiguous := inference in {rel(STAGE)}:{line_no}")
    return issues


def validate_runtime_output() -> List[str]:
    issues: List[str] = []
    data = read_json(GODOT_OUTPUT)
    if data.get("schema") != "boqsc.transvoxel.godot_m4_scripted_edit_compare.v1":
        issues.append("unexpected runtime schema")
    if data.get("status") != "PASS":
        issues.append("runtime status is not PASS")
    if data.get("official_transvoxel_cpp_byte_identity") != "NOT_PROVEN":
        issues.append("official byte identity claim is not NOT_PROVEN")
    if data.get("official_triangle_topology_equivalence") != "NOT_PROVEN":
        issues.append("official topology equivalence claim is not NOT_PROVEN")
    if data.get("default_core_replaced") is not False:
        issues.append("default_core_replaced is not false")
    if data.get("selected_backends") != ["default_independent", "m4_candidate"]:
        issues.append("selected_backends does not list default then M4")

    comparison = data.get("comparison", {})
    if comparison.get("status") != "PASS":
        issues.append("comparison status is not PASS")
    if int(comparison.get("scenario_count", 0)) < 10:
        issues.append("scenario_count is too small")
    if int(comparison.get("scripted_edits", 0)) < 100:
        issues.append("scripted_edits is too small")
    check_count = int(comparison.get("check_count", 0))
    if check_count < 100:
        issues.append("check_count is too small")
    if int(comparison.get("failed_checks", -1)) != 0:
        issues.append("failed_checks is not 0")
    if int(comparison.get("failed_scenarios", -1)) != 0:
        issues.append("failed_scenarios is not 0")
    if int(comparison.get("changed_after_edit_checks", 0)) <= 0:
        issues.append("no edited checks changed the case sequence")
    if int(comparison.get("scenarios_with_changes", 0)) != int(comparison.get("scenario_count", -1)):
        issues.append("not every scenario had an edit that changed the case sequence")
    if int(comparison.get("structurally_distinct_checks", -1)) != check_count:
        issues.append("not every check was structurally distinct between default and M4")
    if int(comparison.get("default_triangles_total", 0)) <= int(comparison.get("m4_triangles_total", 0)):
        issues.append("expected default total triangles to exceed M4 total triangles")
    if comparison.get("default_backend_by_default") is not True:
        issues.append("default_backend_by_default is not true")
    if comparison.get("m4_requires_explicit_selection") is not True:
        issues.append("m4_requires_explicit_selection is not true")
    return issues


def comparison_summary(comparison: Dict[str, Any]) -> Dict[str, Any]:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-output", action="store_true", help="Fail unless the Godot runtime output exists and validates.")
    args = parser.parse_args()

    issues = validate_stage_source()
    runtime_executed = GODOT_OUTPUT.exists()
    if runtime_executed:
        try:
            issues.extend(validate_runtime_output())
        except Exception as exc:
            issues.append("failed to validate runtime output: " + repr(exc))
    elif args.require_output:
        issues.append("missing " + rel(GODOT_OUTPUT))

    status = "PASS_M4_GODOT_SCRIPTED_EDIT_COMPARE" if not issues and runtime_executed else "BLOCKED_M4_GODOT_SCRIPTED_EDIT_COMPARE_NOT_RUN"
    if issues:
        status = "FAIL_M4_GODOT_SCRIPTED_EDIT_COMPARE" if args.require_output or runtime_executed else "FAIL_M4_GODOT_SCRIPTED_EDIT_COMPARE_STAGE_SOURCE"

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_godot_scripted_edit_compare_report.v1",
        "status": status,
        "meaning": (
            "Validates the optional Godot scripted-edit default-vs-M4 comparison "
            "path. PASS requires a real Godot output with edited case-sequence "
            "changes and valid ArrayMesh/MeshDataTool output for both backends."
        ),
        "godot_runtime_executed": runtime_executed,
        "stage": rel(STAGE),
        "runtime_output": rel(GODOT_OUTPUT),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "issues": issues,
    }
    if runtime_executed:
        data = read_json(GODOT_OUTPUT)
        report["runtime_status"] = data.get("status")
        report["comparison"] = comparison_summary(data.get("comparison", {}))

    write_json(REPORT, report)
    print("M4 Godot scripted edit compare:", report["status"])
    if runtime_executed:
        comparison = report.get("comparison", {})
        print(
            "checks={checks} edits={edits} changed={changed} default_tris={default_tris} m4_tris={m4_tris}".format(
                checks=comparison.get("check_count") if isinstance(comparison, dict) else None,
                edits=comparison.get("scripted_edits") if isinstance(comparison, dict) else None,
                changed=comparison.get("changed_after_edit_checks") if isinstance(comparison, dict) else None,
                default_tris=comparison.get("default_triangles_total") if isinstance(comparison, dict) else None,
                m4_tris=comparison.get("m4_triangles_total") if isinstance(comparison, dict) else None,
            )
        )
    if issues:
        for issue in issues:
            print("issue:", issue)
    return 0 if not issues and (runtime_executed or not args.require_output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
