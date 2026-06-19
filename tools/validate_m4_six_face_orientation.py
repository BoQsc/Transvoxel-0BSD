#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate M15 C/Godot six-face M4 orientation evidence."""
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
    / "11_m4_six_face_orientation"
    / "DumpM4SixFaceOrientation.gd"
)
GODOT_OUTPUT = (
    ROOT
    / "godot"
    / "validation"
    / "11_m4_six_face_orientation"
    / "m4_six_face_orientation.json"
)
C_REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m15"
    / "m15_c_validation.json"
)
REPORT = ROOT / "validation" / "m4_six_face_orientation_report.json"

EXPECTED_FRAMES = [
    {
        "id": 0,
        "name": "positive_x",
        "axis_u": [0.0, 1.0, 0.0],
        "axis_v": [0.0, 0.0, 1.0],
        "axis_w": [1.0, 0.0, 0.0],
    },
    {
        "id": 1,
        "name": "negative_x",
        "axis_u": [0.0, -1.0, 0.0],
        "axis_v": [0.0, 0.0, 1.0],
        "axis_w": [-1.0, 0.0, 0.0],
    },
    {
        "id": 2,
        "name": "positive_y",
        "axis_u": [0.0, 0.0, 1.0],
        "axis_v": [1.0, 0.0, 0.0],
        "axis_w": [0.0, 1.0, 0.0],
    },
    {
        "id": 3,
        "name": "negative_y",
        "axis_u": [0.0, 0.0, -1.0],
        "axis_v": [1.0, 0.0, 0.0],
        "axis_w": [0.0, -1.0, 0.0],
    },
    {
        "id": 4,
        "name": "positive_z",
        "axis_u": [1.0, 0.0, 0.0],
        "axis_v": [0.0, 1.0, 0.0],
        "axis_w": [0.0, 0.0, 1.0],
    },
    {
        "id": 5,
        "name": "negative_z",
        "axis_u": [-1.0, 0.0, 0.0],
        "axis_v": [0.0, 1.0, 0.0],
        "axis_w": [0.0, 0.0, -1.0],
    },
]

FACE_METRICS = [
    "cases",
    "vertices",
    "triangles",
    "invalid_triangles",
    "degenerate_triangles",
    "transform_failures",
    "orientation_failures",
    "frame_failures",
    "seam_builds",
    "shared_faces",
    "seam_failures",
    "seam_vertices",
    "seam_triangles",
]

EXPECTED_FACE = {
    "cases": 512,
    "vertices": 4096,
    "triangles": 2640,
    "invalid_triangles": 0,
    "degenerate_triangles": 0,
    "transform_failures": 0,
    "orientation_failures": 0,
    "frame_failures": 0,
    "seam_builds": 448,
    "shared_faces": 672,
    "seam_failures": 0,
    "seam_vertices": 1616,
    "seam_triangles": 1020,
}

EXPECTED_TOTALS = {
    "faces": 6,
    "failed_faces": 0,
    "cases": 3072,
    "vertices": 24576,
    "triangles": 15840,
    "invalid_triangles": 0,
    "degenerate_triangles": 0,
    "transform_failures": 0,
    "orientation_failures": 0,
    "frame_failures": 0,
    "seam_builds": 2688,
    "shared_faces": 4032,
    "seam_failures": 0,
    "seam_vertices": 9696,
    "seam_triangles": 6120,
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
        "_face_specs",
        "_frame_to_local",
        "_expected_transformed_cross",
        "_validate_face_cases",
        "_validate_face_seams",
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


def validate_c_report(data: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    if data.get("schema") != "boqsc.transvoxel.official_topology.m15.c_validation.v1":
        issues.append("unexpected C report schema")
    if data.get("status") != "PASS_M15_ZIG_M4_SIX_FACE_ORIENTATION_VALIDATION":
        issues.append("C report status is not PASS")
    if data.get("compiler") != "zig cc":
        issues.append("C report compiler is not zig cc")
    faces = data.get("faces", [])
    if not isinstance(faces, list) or len(faces) != 6:
        issues.append("C report does not contain six face records")
    else:
        for face_id, face in enumerate(faces):
            if int(face.get("id", -1)) != face_id:
                issues.append(f"C face {face_id} id mismatch")
            for key, expected in EXPECTED_FACE.items():
                if int(face.get(key, -1)) != expected:
                    issues.append(
                        f"C face {face_id} {key} expected {expected}, got {face.get(key)}"
                    )
    totals = data.get("totals", {})
    for key, expected in EXPECTED_TOTALS.items():
        if int(totals.get(key, -1)) != expected:
            issues.append(
                f"C totals {key} expected {expected}, got {totals.get(key)}"
            )
    return issues


def numbers_equal(a: Any, b: Any) -> bool:
    try:
        return abs(float(a) - float(b)) <= 0.00001
    except (TypeError, ValueError):
        return False


def vectors_equal(a: Any, b: Any) -> bool:
    return (
        isinstance(a, list)
        and isinstance(b, list)
        and len(a) == 3
        and len(b) == 3
        and all(numbers_equal(a[index], b[index]) for index in range(3))
    )


def validate_godot_output(
    data: Dict[str, Any],
    c_report: Dict[str, Any],
) -> List[str]:
    issues: List[str] = []
    if data.get("schema") != "boqsc.transvoxel.godot_m4_six_face_orientation.v1":
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
    godot_faces = validation.get("faces", [])
    c_faces = c_report.get("faces", [])
    if not isinstance(godot_faces, list) or len(godot_faces) != 6:
        issues.append("Godot output does not contain six face records")
    else:
        for face_id, face in enumerate(godot_faces):
            expected_frame = EXPECTED_FRAMES[face_id]
            if int(face.get("id", -1)) != expected_frame["id"]:
                issues.append(f"Godot face {face_id} id mismatch")
            if face.get("name") != expected_frame["name"]:
                issues.append(f"Godot face {face_id} name mismatch")
            for axis in ["axis_u", "axis_v", "axis_w"]:
                if not vectors_equal(face.get(axis), expected_frame[axis]):
                    issues.append(f"Godot face {face_id} {axis} mismatch")
            if not numbers_equal(face.get("determinant"), 1.0):
                issues.append(f"Godot face {face_id} determinant is not +1")
            if face.get("status") != "PASS":
                issues.append(f"Godot face {face_id} status is not PASS")
            for key, expected in EXPECTED_FACE.items():
                if int(face.get(key, -1)) != expected:
                    issues.append(
                        f"Godot face {face_id} {key} expected {expected}, got {face.get(key)}"
                    )
                if (
                    isinstance(c_faces, list)
                    and len(c_faces) == 6
                    and int(face.get(key, -1)) != int(c_faces[face_id].get(key, -2))
                ):
                    issues.append(f"C/Godot face {face_id} {key} mismatch")
            mesh = face.get("mesh", {})
            if mesh.get("status") != "PASS":
                issues.append(f"Godot face {face_id} ArrayMesh status is not PASS")
            if int(mesh.get("mdt_faces", -1)) != EXPECTED_FACE["triangles"]:
                issues.append(f"Godot face {face_id} MeshDataTool face count mismatch")

    godot_totals = validation.get("totals", {})
    c_totals = c_report.get("totals", {})
    for key, expected in EXPECTED_TOTALS.items():
        if int(godot_totals.get(key, -1)) != expected:
            issues.append(
                f"Godot totals {key} expected {expected}, got {godot_totals.get(key)}"
            )
        if int(godot_totals.get(key, -1)) != int(c_totals.get(key, -2)):
            issues.append(f"C/Godot totals {key} mismatch")
    return issues


def face_summary(face: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "id": face.get("id"),
        "name": face.get("name"),
        "status": face.get("status"),
        "determinant": face.get("determinant"),
    }
    for key in FACE_METRICS:
        summary[key] = face.get(key)
    mesh = face.get("mesh", {})
    if isinstance(mesh, dict):
        summary["mesh"] = {
            "status": mesh.get("status"),
            "surface_count": mesh.get("surface_count"),
            "mdt_error": mesh.get("mdt_error"),
            "mdt_vertices": mesh.get("mdt_vertices"),
            "mdt_edges": mesh.get("mdt_edges"),
            "mdt_faces": mesh.get("mdt_faces"),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-output",
        action="store_true",
        help="Fail unless the real Godot runtime output exists and validates.",
    )
    args = parser.parse_args()

    issues = validate_stage_source()
    c_executed = C_REPORT.exists()
    godot_executed = GODOT_OUTPUT.exists()
    c_report: Dict[str, Any] = {}
    godot_data: Dict[str, Any] = {}

    if c_executed:
        try:
            c_report = read_json(C_REPORT)
            issues.extend(validate_c_report(c_report))
        except Exception as exc:
            issues.append("failed to validate C report: " + repr(exc))
    else:
        issues.append("missing " + rel(C_REPORT))

    if godot_executed:
        try:
            godot_data = read_json(GODOT_OUTPUT)
            issues.extend(validate_godot_output(godot_data, c_report))
        except Exception as exc:
            issues.append("failed to validate Godot output: " + repr(exc))
    elif args.require_output:
        issues.append("missing " + rel(GODOT_OUTPUT))

    if issues:
        status = "FAIL_M4_SIX_FACE_ORIENTATION_VALIDATION"
    elif godot_executed:
        status = "PASS_M4_SIX_FACE_ORIENTATION_C_AND_GODOT"
    else:
        status = "BLOCKED_M4_SIX_FACE_ORIENTATION_GODOT_NOT_RUN"

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_six_face_orientation_report.v1",
        "status": status,
        "meaning": (
            "PASS requires Zig-compiled C and actual Godot runtime validation "
            "of all 512 M4 cases and deterministic neighbor seams in all six "
            "explicit right-handed transition-face frames."
        ),
        "c_runtime_executed": c_executed,
        "godot_runtime_executed": godot_executed,
        "stage": rel(STAGE),
        "c_report": rel(C_REPORT),
        "godot_runtime_output": rel(GODOT_OUTPUT),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_reference_convention_equivalence": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "issues": issues,
    }
    if c_report:
        report["c_status"] = c_report.get("status")
        report["c_totals"] = c_report.get("totals", {})
    if godot_data:
        validation = godot_data.get("validation", {})
        report["godot_status"] = godot_data.get("status")
        report["godot_totals"] = validation.get("totals", {})
        report["faces"] = [
            face_summary(face)
            for face in validation.get("faces", [])
            if isinstance(face, dict)
        ]

    write_json(REPORT, report)
    print("M4 six-face orientation:", status)
    if c_report:
        print("C totals:", c_report.get("totals", {}))
    if godot_data:
        print("Godot totals:", godot_data.get("validation", {}).get("totals", {}))
    for issue in issues:
        print("issue:", issue)
    return 0 if not issues and (godot_executed or not args.require_output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
