#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the optional M4 Godot viewer/export runtime report.

By default this tool validates that the stage is packaged and, if the Godot
runtime output exists, validates that output. Use --require-output in milestone
runs that are meant to prove actual Godot execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "godot" / "stages" / "08_m4_candidate_viewer" / "DumpM4CandidateViewer.gd"
GODOT_OUTPUT = ROOT / "godot" / "validation" / "08_m4_candidate_viewer" / "m4_candidate_viewer.json"
REPORT = ROOT / "validation" / "m4_godot_viewer_report.json"


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
        "M4_PATH",
        "OUT_PATH",
        "_build_case_gallery",
        "_build_terrain_strip",
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


def validate_runtime_output() -> List[str]:
    issues: List[str] = []
    data = read_json(GODOT_OUTPUT)
    if data.get("schema") != "boqsc.transvoxel.godot_m4_candidate_viewer.v1":
        issues.append("unexpected runtime schema")
    if data.get("status") != "PASS":
        issues.append("runtime status is not PASS")
    if data.get("official_transvoxel_cpp_byte_identity") != "NOT_PROVEN":
        issues.append("official byte identity claim is not NOT_PROVEN")
    if data.get("official_triangle_topology_equivalence") != "NOT_PROVEN":
        issues.append("official topology equivalence claim is not NOT_PROVEN")
    if data.get("default_core_replaced") is not False:
        issues.append("default_core_replaced is not false")

    table = data.get("table", {})
    if table.get("status") != "PASS":
        issues.append("table contract status is not PASS")
    if int(table.get("case_count", 0)) != 512:
        issues.append("table case_count is not 512")
    if int(table.get("sample_count", 0)) != 13:
        issues.append("table sample_count is not 13")
    if int(table.get("research_class_count", 0)) != 73:
        issues.append("table research_class_count is not 73")

    gallery = data.get("case_gallery", {})
    if gallery.get("status") != "PASS":
        issues.append("case gallery status is not PASS")
    if int(gallery.get("non_empty_cases", 0)) < 12:
        issues.append("case gallery has too few non-empty cases")
    validate_mesh_summary(issues, gallery.get("mesh", {}), "case_gallery")

    strip = data.get("terrain_strip", {})
    if strip.get("status") != "PASS":
        issues.append("terrain strip status is not PASS")
    if int(strip.get("non_empty_cells", 0)) <= 0:
        issues.append("terrain strip has no non-empty cells")
    if int(strip.get("grid", 0)) < 4:
        issues.append("terrain strip grid is too small")
    validate_mesh_summary(issues, strip.get("mesh", {}), "terrain_strip")
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

    status = "PASS_M4_GODOT_VIEWER_EXPORT_PATH" if not issues and runtime_executed else "BLOCKED_M4_GODOT_VIEWER_NOT_RUN"
    if issues:
        status = "FAIL_M4_GODOT_VIEWER_EXPORT_PATH" if args.require_output or runtime_executed else "FAIL_M4_GODOT_VIEWER_STAGE_SOURCE"

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_godot_viewer_report.v1",
        "status": status,
        "meaning": (
            "Validates the optional M4 Godot viewer/export path. PASS requires "
            "a real Godot output that builds ArrayMesh objects and validates "
            "MeshDataTool readback."
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
        report["case_gallery"] = data.get("case_gallery", {})
        report["terrain_strip"] = data.get("terrain_strip", {})

    write_json(REPORT, report)
    print("M4 Godot viewer:", report["status"])
    if runtime_executed:
        strip = report.get("terrain_strip", {})
        mesh = strip.get("mesh", {}) if isinstance(strip, dict) else {}
        print(
            "m4 viewer strip cells={cells} vertices={vertices} triangles={triangles}".format(
                cells=strip.get("non_empty_cells") if isinstance(strip, dict) else None,
                vertices=mesh.get("array_vertex_count") if isinstance(mesh, dict) else None,
                triangles=mesh.get("triangle_count") if isinstance(mesh, dict) else None,
            )
        )
    if issues:
        for issue in issues:
            print("issue:", issue)
    return 0 if not issues and (runtime_executed or not args.require_output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
