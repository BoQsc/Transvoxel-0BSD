#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build the M4-selected production-readiness gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "proof" / "m4_production_gate.json"

EXPECTED_REPORTS: List[Tuple[str, Path, str]] = [
    (
        "m4_backend_normal_api",
        ROOT / "validation" / "m4_backend_c_report.json",
        "PASS_M4_BACKEND_PACKAGE_C_EXAMPLE",
    ),
    (
        "m4_terrain_normal_api",
        ROOT / "validation" / "m4_terrain_c_report.json",
        "PASS_M4_TERRAIN_NORMAL_API_EXPORT",
    ),
    (
        "m4_scripted_edits",
        ROOT / "research" / "official_topology" / "m13" / "m13_report.json",
        "PASS_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    (
        "m4_six_faces",
        ROOT / "research" / "official_topology" / "m15" / "m15_report.json",
        "PASS_M15_M4_SIX_FACE_ORIENTATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    (
        "m4_corner_junctions",
        ROOT / "research" / "official_topology" / "m16" / "m16_report.json",
        "PASS_M16_M4_DEFORMED_CORNER_JUNCTIONS_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    (
        "m4_combined_c_assembler",
        ROOT / "research" / "official_topology" / "m17" / "m17_c_validation.json",
        "PASS_M17_ZIG_M4_SELECTED_PRODUCTION_ASSEMBLER",
    ),
    (
        "m4_six_face_validation",
        ROOT / "validation" / "m4_six_face_orientation_report.json",
        "PASS_M4_SIX_FACE_ORIENTATION_C_AND_GODOT",
    ),
    (
        "m4_corner_validation",
        ROOT / "validation" / "m4_corner_junction_report.json",
        "PASS_M4_DEFORMED_CORNER_JUNCTIONS_C_AND_GODOT",
    ),
]

EXPECTED_RUNTIME_OUTPUTS: List[Tuple[str, Path, str]] = [
    (
        "scripted_edits",
        ROOT
        / "godot"
        / "validation"
        / "10_m4_scripted_edit_compare"
        / "m4_scripted_edit_compare.json",
        "PASS",
    ),
    (
        "six_faces",
        ROOT
        / "godot"
        / "validation"
        / "11_m4_six_face_orientation"
        / "m4_six_face_orientation.json",
        "PASS",
    ),
    (
        "corner_junctions",
        ROOT
        / "godot"
        / "validation"
        / "12_m4_corner_junctions"
        / "m4_corner_junctions.json",
        "PASS",
    ),
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    checks: List[Dict[str, Any]] = []
    issues: List[str] = []

    for check_id, path, expected in EXPECTED_REPORTS:
        if not path.exists():
            actual = "MISSING"
            issues.append("missing " + rel(path))
        else:
            try:
                data = read_json(path)
                actual = str(data.get("status", "MISSING_STATUS"))
            except Exception as exc:
                actual = "INVALID_JSON"
                issues.append(f"invalid {rel(path)}: {exc!r}")
        if actual != expected:
            issues.append(f"{check_id}: expected {expected}, got {actual}")
        checks.append({
            "id": check_id,
            "path": rel(path),
            "actual": actual,
            "expected": expected,
            "status": "PASS" if actual == expected else "FAIL",
        })

    for check_id, path, expected in EXPECTED_RUNTIME_OUTPUTS:
        if not path.exists():
            actual = "MISSING"
            issues.append("missing " + rel(path))
        else:
            try:
                data = read_json(path)
                actual = str(data.get("status", "MISSING_STATUS"))
            except Exception as exc:
                actual = "INVALID_JSON"
                issues.append(f"invalid {rel(path)}: {exc!r}")
        if actual != expected:
            issues.append(f"runtime {check_id}: expected {expected}, got {actual}")
        checks.append({
            "id": "godot_runtime_" + check_id,
            "path": rel(path),
            "actual": actual,
            "expected": expected,
            "status": "PASS" if actual == expected else "FAIL",
        })

    base_gate_path = ROOT / "proof" / "production_gate.json"
    base_gate_status = "MISSING"
    if base_gate_path.exists():
        try:
            base_gate_status = str(read_json(base_gate_path).get("status", "MISSING_STATUS"))
        except Exception as exc:
            issues.append("invalid proof/production_gate.json: " + repr(exc))
    if base_gate_status != "PASS":
        issues.append(
            "base production gate expected PASS, got " + base_gate_status
        )
    checks.append({
        "id": "base_production_gate",
        "path": rel(base_gate_path),
        "actual": base_gate_status,
        "expected": "PASS",
        "status": "PASS" if base_gate_status == "PASS" else "FAIL",
    })

    m4_table = read_json(
        ROOT / "generated" / "official_topology_candidate_tables.json"
    )
    m4_validation = read_json(
        ROOT
        / "research"
        / "official_topology"
        / "m4"
        / "runtime_table_validation.json"
    )
    if int(m4_validation.get("case_winding_failure_count", -1)) != 0:
        issues.append("M4 case winding failures are not zero")
    reference_path = ROOT / "validation" / "reference_convention_matrix.json"
    reference_status = "NOT_PROVEN"
    if reference_path.exists():
        reference_status = str(
            read_json(reference_path).get(
                "official_reference_equivalence",
                "NOT_PROVEN",
            )
        )

    status = (
        "PASS_M4_SELECTED_PRODUCTION_GATE"
        if not issues
        else "FAIL_M4_SELECTED_PRODUCTION_GATE"
    )
    result: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_production_gate.v1",
        "status": status,
        "meaning": (
            "PASS proves the clean-room M4 transition candidate can run through "
            "the normal C backend hook, terrain export, Godot scripted edits, "
            "all six face frames, mapped corner junctions, and the existing base "
            "production gate. Published reference convention evidence is "
            "reported separately; topology and full replacement equivalence "
            "are not proven by this gate."
        ),
        "m4_table_sha256": m4_table.get("sha256_without_this_field"),
        "m4_case_winding_failure_count": m4_validation.get(
            "case_winding_failure_count"
        ),
        "checks": checks,
        "issues": issues,
        "hard_requirements": {
            "normal_api_backend_install": True,
            "normal_api_all_512_cases": True,
            "terrain_export": True,
            "godot_scripted_edits": True,
            "all_six_face_orientations": True,
            "mapped_three_face_corner_junctions": True,
            "base_production_gate": True,
            "invalid_triangles": 0,
            "degenerate_triangles": 0,
            "seam_failures": 0,
            "winding_failures": 0,
        },
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_reference_convention_equivalence": reference_status,
        "official_triangle_topology_equivalence": "NOT_PROVEN",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("M4 production gate:", status)
    for issue in issues:
        print("issue:", issue)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
