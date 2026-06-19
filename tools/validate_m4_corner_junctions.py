#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate M16 mapped M4 corner-junction evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
STAGE = (
    ROOT
    / "godot"
    / "stages"
    / "12_m4_corner_junctions"
    / "DumpM4CornerJunctions.gd"
)
GODOT_OUTPUT = (
    ROOT
    / "godot"
    / "validation"
    / "12_m4_corner_junctions"
    / "m4_corner_junctions.json"
)
C_REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m16"
    / "m16_c_validation.json"
)
M4_VALIDATION = (
    ROOT
    / "research"
    / "official_topology"
    / "m4"
    / "runtime_table_validation.json"
)
REPORT = ROOT / "validation" / "m4_corner_junction_report.json"

EXPECTED = {
    "octants": 8,
    "fields": 7,
    "seeds": 8,
    "junctions": 448,
    "builds": 1344,
    "vertices": 4680,
    "triangles": 2896,
    "invalid_triangles": 0,
    "degenerate_triangles": 0,
    "internal_winding_failures": 0,
    "shared_faces": 1344,
    "nonempty_shared_faces": 500,
    "shared_samples": 6720,
    "sample_position_failures": 0,
    "sample_value_failures": 0,
    "lateral_geometry_failures": 0,
    "lateral_winding_failures": 0,
    "corner_position_failures": 0,
    "corner_value_failures": 0,
}


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
        "_mapped_sample_positions",
        "_corner_frames",
        "_compare_shared_samples",
        "_compare_fingerprints",
        "_validate_cell",
        "ArrayMesh",
        "MeshDataTool",
    ]:
        if token not in text:
            issues.append(f"stage missing token {token}")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and ":=" in stripped:
            issues.append(f"ambiguous := inference in {rel(STAGE)}:{line_no}")
    return issues


def validate_metrics(
    label: str,
    metrics: Dict[str, Any],
) -> List[str]:
    issues: List[str] = []
    for key, expected in EXPECTED.items():
        if int(metrics.get(key, -1)) != expected:
            issues.append(
                f"{label} {key} expected {expected}, got {metrics.get(key)}"
            )
    return issues


def validate_c_report(data: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    if data.get("schema") != "boqsc.transvoxel.official_topology.m16.c_validation.v1":
        issues.append("unexpected C report schema")
    if data.get("status") != "PASS_M16_ZIG_M4_DEFORMED_CORNER_JUNCTIONS":
        issues.append("C report status is not PASS")
    if data.get("compiler") != "zig cc":
        issues.append("C report compiler is not zig cc")
    issues.extend(validate_metrics("C", data.get("metrics", {})))
    return issues


def validate_m4_winding(data: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    if data.get("status") != "PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN":
        issues.append("M4 runtime table validation is not PASS")
    if int(data.get("case_winding_failure_count", -1)) != 0:
        issues.append("M4 runtime table winding failures are not zero")
    return issues


def validate_godot_output(
    data: Dict[str, Any],
    c_report: Dict[str, Any],
) -> List[str]:
    issues: List[str] = []
    if data.get("schema") != "boqsc.transvoxel.godot_m4_corner_junctions.v1":
        issues.append("unexpected Godot output schema")
    if data.get("status") != "PASS":
        issues.append("Godot output status is not PASS")
    for key in [
        "official_transvoxel_cpp_byte_identity",
        "official_reference_convention_equivalence",
        "official_triangle_topology_equivalence",
    ]:
        if data.get(key) != "NOT_PROVEN":
            issues.append(f"{key} claim is not NOT_PROVEN")
    if data.get("default_core_replaced") is not False:
        issues.append("default_core_replaced is not false")
    validation = data.get("validation", {})
    if validation.get("status") != "PASS":
        issues.append("Godot validation status is not PASS")
    metrics = validation.get("totals", {})
    issues.extend(validate_metrics("Godot", metrics))
    c_metrics = c_report.get("metrics", {})
    for key in EXPECTED:
        if int(metrics.get(key, -1)) != int(c_metrics.get(key, -2)):
            issues.append(f"C/Godot {key} mismatch")
    mesh = validation.get("mesh", {})
    if mesh.get("status") != "PASS":
        issues.append("Godot ArrayMesh status is not PASS")
    if int(mesh.get("mdt_faces", -1)) != EXPECTED["triangles"]:
        issues.append("Godot MeshDataTool face count mismatch")
    if int(mesh.get("mdt_vertices", -1)) != EXPECTED["vertices"]:
        issues.append("Godot MeshDataTool vertex count mismatch")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-output",
        action="store_true",
        help="Fail unless actual Godot runtime output exists and validates.",
    )
    args = parser.parse_args()

    issues = validate_stage_source()
    c_executed = C_REPORT.exists()
    godot_executed = GODOT_OUTPUT.exists()
    c_report: Dict[str, Any] = {}
    godot_data: Dict[str, Any] = {}
    m4_validation: Dict[str, Any] = {}

    if C_REPORT.exists():
        try:
            c_report = read_json(C_REPORT)
            issues.extend(validate_c_report(c_report))
        except Exception as exc:
            issues.append("failed to validate C report: " + repr(exc))
    else:
        issues.append("missing " + rel(C_REPORT))

    if M4_VALIDATION.exists():
        try:
            m4_validation = read_json(M4_VALIDATION)
            issues.extend(validate_m4_winding(m4_validation))
        except Exception as exc:
            issues.append("failed to validate M4 winding report: " + repr(exc))
    else:
        issues.append("missing " + rel(M4_VALIDATION))

    if GODOT_OUTPUT.exists():
        try:
            godot_data = read_json(GODOT_OUTPUT)
            issues.extend(validate_godot_output(godot_data, c_report))
        except Exception as exc:
            issues.append("failed to validate Godot output: " + repr(exc))
    elif args.require_output:
        issues.append("missing " + rel(GODOT_OUTPUT))

    if issues:
        status = "FAIL_M4_CORNER_JUNCTION_VALIDATION"
    elif godot_executed:
        status = "PASS_M4_DEFORMED_CORNER_JUNCTIONS_C_AND_GODOT"
    else:
        status = "BLOCKED_M4_CORNER_JUNCTIONS_GODOT_NOT_RUN"

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_corner_junction_report.v1",
        "status": status,
        "meaning": (
            "PASS requires coherent clean-room M4 table winding plus "
            "Zig-compiled C and actual Godot runtime evidence for three mapped "
            "transition cells meeting at every signed corner octant."
        ),
        "c_runtime_executed": c_executed,
        "godot_runtime_executed": godot_executed,
        "stage": rel(STAGE),
        "c_report": rel(C_REPORT),
        "m4_winding_report": rel(M4_VALIDATION),
        "godot_runtime_output": rel(GODOT_OUTPUT),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_reference_convention_equivalence": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "issues": issues,
    }
    if c_report:
        report["c_status"] = c_report.get("status")
        report["c_metrics"] = c_report.get("metrics", {})
    if m4_validation:
        report["m4_winding_status"] = m4_validation.get("status")
        report["m4_case_winding_failure_count"] = m4_validation.get(
            "case_winding_failure_count"
        )
    if godot_data:
        validation = godot_data.get("validation", {})
        report["godot_status"] = godot_data.get("status")
        report["godot_metrics"] = validation.get("totals", {})
        report["godot_mesh"] = validation.get("mesh", {})

    write_json(REPORT, report)
    print("M4 corner junctions:", status)
    if c_report:
        print("C metrics:", c_report.get("metrics", {}))
    if godot_data:
        print("Godot metrics:", godot_data.get("validation", {}).get("totals", {}))
    for issue in issues:
        print("issue:", issue)
    return 0 if not issues and (godot_executed or not args.require_output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
