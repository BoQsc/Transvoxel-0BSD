#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the optional M4/default Godot backend comparison report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "godot" / "stages" / "09_m4_backend_compare" / "DumpM4BackendCompare.gd"
GODOT_OUTPUT = ROOT / "godot" / "validation" / "09_m4_backend_compare" / "m4_backend_compare.json"
REPORT = ROOT / "validation" / "m4_godot_backend_compare_report.json"


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
        "_build_backend",
        "_compare_backends",
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


def require_int_at_least(issues: List[str], data: Dict[str, Any], key: str, minimum: int, label: str) -> None:
    value = int(data.get(key, 0))
    if value < minimum:
        issues.append(f"{label} {key} is {value}, expected >= {minimum}")


def validate_mesh_summary(issues: List[str], mesh: Dict[str, Any], label: str) -> None:
    if mesh.get("status") != "PASS":
        issues.append(label + " mesh status is not PASS")
    require_int_at_least(issues, mesh, "surface_count", 1, label)
    require_int_at_least(issues, mesh, "array_vertex_count", 1, label)
    require_int_at_least(issues, mesh, "triangle_count", 1, label)
    if int(mesh.get("mdt_create_error", -1)) != 0:
        issues.append(label + " MeshDataTool create error is not OK")
    if int(mesh.get("invalid_triangles", -1)) != 0:
        issues.append(label + " invalid_triangles is not 0")
    if int(mesh.get("degenerate_triangles", -1)) != 0:
        issues.append(label + " degenerate_triangles is not 0")


def validate_backend(issues: List[str], backend: Dict[str, Any], label: str) -> None:
    if backend.get("status") != "PASS":
        issues.append(label + " backend status is not PASS")
    require_int_at_least(issues, backend, "case_count", 512, label)
    require_int_at_least(issues, backend, "sample_count", 1, label)
    require_int_at_least(issues, backend, "non_empty_cells", 1, label)
    require_int_at_least(issues, backend, "appended_vertices", 1, label)
    require_int_at_least(issues, backend, "appended_triangles", 1, label)
    validate_mesh_summary(issues, backend.get("mesh", {}), label)


def validate_runtime_output() -> List[str]:
    issues: List[str] = []
    data = read_json(GODOT_OUTPUT)
    if data.get("schema") != "boqsc.transvoxel.godot_m4_backend_compare.v1":
        issues.append("unexpected runtime schema")
    if data.get("status") != "PASS":
        issues.append("runtime status is not PASS")
    if data.get("official_transvoxel_cpp_byte_identity") != "NOT_PROVEN":
        issues.append("official byte identity claim is not NOT_PROVEN")
    if data.get("official_triangle_topology_equivalence") != "NOT_PROVEN":
        issues.append("official topology equivalence claim is not NOT_PROVEN")
    if data.get("default_core_replaced") is not False:
        issues.append("default_core_replaced is not false")

    selected = data.get("selected_backends", [])
    if selected != ["default_independent", "m4_candidate"]:
        issues.append("selected_backends does not list default then M4")

    default_backend = data.get("default_backend", {})
    m4_backend = data.get("m4_backend", {})
    validate_backend(issues, default_backend, "default")
    validate_backend(issues, m4_backend, "m4")
    if default_backend.get("schema") != "boqsc.transition_tables.v1":
        issues.append("default backend schema mismatch")
    if m4_backend.get("schema") != "boqsc.transvoxel.official_topology.m4.runtime_candidate.v1":
        issues.append("M4 backend schema mismatch")

    comparison = data.get("comparison", {})
    if comparison.get("same_case_sequence") is not True:
        issues.append("comparison same_case_sequence is not true")
    if comparison.get("same_non_empty_cell_count") is not True:
        issues.append("comparison same_non_empty_cell_count is not true")
    if comparison.get("m4_structurally_distinct_from_default") is not True:
        issues.append("M4 was not structurally distinct from default")
    if comparison.get("default_backend_by_default") is not True:
        issues.append("default_backend_by_default is not true")
    if comparison.get("m4_requires_explicit_selection") is not True:
        issues.append("m4_requires_explicit_selection is not true")
    if int(comparison.get("default_triangles", 0)) == int(comparison.get("m4_triangles", 0)):
        issues.append("default and M4 triangle counts did not differ")
    return issues


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

    status = "PASS_M4_GODOT_BACKEND_COMPARE" if not issues and runtime_executed else "BLOCKED_M4_GODOT_BACKEND_COMPARE_NOT_RUN"
    if issues:
        status = "FAIL_M4_GODOT_BACKEND_COMPARE" if args.require_output or runtime_executed else "FAIL_M4_GODOT_BACKEND_COMPARE_STAGE_SOURCE"

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_godot_backend_compare_report.v1",
        "status": status,
        "meaning": (
            "Validates the optional Godot default-vs-M4 backend comparison path. "
            "PASS requires a real Godot output that builds both ArrayMesh outputs "
            "and proves M4 remains explicitly selected."
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
        report["default_backend"] = data.get("default_backend", {})
        report["m4_backend"] = data.get("m4_backend", {})
        report["comparison"] = data.get("comparison", {})

    write_json(REPORT, report)
    print("M4 Godot backend compare:", report["status"])
    if runtime_executed:
        comparison = report.get("comparison", {})
        print(
            "default triangles={default_triangles} m4 triangles={m4_triangles} delta={delta}".format(
                default_triangles=comparison.get("default_triangles") if isinstance(comparison, dict) else None,
                m4_triangles=comparison.get("m4_triangles") if isinstance(comparison, dict) else None,
                delta=comparison.get("triangle_delta_m4_minus_default") if isinstance(comparison, dict) else None,
            )
        )
    if issues:
        for issue in issues:
            print("issue:", issue)
    return 0 if not issues and (runtime_executed or not args.require_output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
