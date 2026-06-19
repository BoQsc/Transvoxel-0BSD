#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Aggregate strict correctness audit reports into a single proof matrix."""
from __future__ import annotations

import json
import runpy
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"

STEPS = [
    "tools/validate_73_classes.py",
    "tools/validate_winding_normals.py",
    "tools/validate_self_intersections.py",
    "tools/validate_reference_convention.py",
    "tools/validate_corner_junctions.py",
    "tools/topology_signature_analysis.py",
]

REPORT_FILES = {
    "73_classes": "validation/equivalence_class_report.json",
    "winding_normals": "validation/winding_normals_report.json",
    "self_intersections": "validation/self_intersection_report.json",
    "reference_convention": "validation/reference_convention_report.json",
    "corner_junctions": "validation/corner_junction_report.json",
    "topology_signatures": "validation/topology_signature_report.json",
    "official_73_candidate_derivation": "validation/official_73_candidate_derivation.json",
    "reference_convention_matrix": "validation/reference_convention_matrix.json",
    "official_topology_constraints": "validation/official_topology_constraints.json",
}


def run_step(path: str) -> Dict[str, Any]:
    old_argv = sys.argv[:]
    start = time.monotonic()
    code: Any = 0
    ok = False
    print("RUN", path, flush=True)
    try:
        sys.argv = [str(ROOT / path)]
        try:
            runpy.run_path(str(ROOT / path), run_name="__main__")
            code = 0
            ok = True
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 0
            ok = code == 0
    except BaseException as exc:
        code = type(exc).__name__
        ok = False
        print("ERROR", path, repr(exc), flush=True)
    finally:
        sys.argv = old_argv
    elapsed = time.monotonic() - start
    print(("PASS" if ok else "FAIL"), path, f"{elapsed:.2f}s", flush=True)
    return {"command": path, "ok": ok, "returncode": code, "elapsed_seconds": round(elapsed, 3)}


def read_json(rel: str) -> Dict[str, Any]:
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "MISSING", "path": rel}


def main() -> int:
    VALIDATION.mkdir(exist_ok=True)
    steps = [run_step(s) for s in STEPS]
    reports = {name: read_json(rel) for name, rel in REPORT_FILES.items()}
    hard_fail = not all(bool(s["ok"]) for s in steps)
    matrix = {
        "every_512_transition_case_internally_valid": "PASS" if read_json("validation/boundary_report.json").get("status") == "PASS" else "NOT_PROVEN",
        "official_73_equivalence_classes_mapped": "NOT_PROVEN",
        "official_73_candidate_derivation_status": reports.get("official_73_candidate_derivation", {}).get("status", "MISSING"),
        "generated_topology_signature_matches_official_73_count": "NOT_PROVEN" if reports["topology_signatures"].get("matches_official_73_count") else "MISMATCH_OR_NOT_PROVEN",
        "generated_topology_signature_closest_to_73": reports["topology_signatures"].get("closest_count_to_official_target", {}),
        "triangle_winding_normals_internal_consistency": reports["winding_normals"].get("status", "UNKNOWN"),
        "no_duplicate_triangles_in_generated_cases": "PASS" if reports["winding_normals"].get("status") == "PASS" else "NOT_PROVEN",
        "no_zero_area_degenerate_triangles_in_generated_cases": "PASS" if reports["winding_normals"].get("status") == "PASS" else "NOT_PROVEN",
        "no_generated_case_self_intersections_midpoint_geometry": reports["self_intersections"].get("status", "UNKNOWN"),
        "same_orientation_sign_convention_as_reference": (
            reports["reference_convention"].get(
                "reference_equivalence_status",
                "NOT_PROVEN",
            )
        ),
        "internal_reference_convention_matrix": reports.get("reference_convention_matrix", {}).get("status", "MISSING"),
        "edited_terrain_all_six_faces_scripted": "PASS" if (
            reports["corner_junctions"].get("tested_face_directions", 0) >= 6
            and reports["corner_junctions"].get("tested_fields", 0) >= 5
            and reports["corner_junctions"].get("scripted_edits", 0) >= 100
            and reports["corner_junctions"].get("failed_auto_checks", 1) == 0
        ) else "NOT_PROVEN_OR_NOT_RUN",
        "all_corners_and_multi_neighbor_production_junctions": "NOT_FULLY_PROVEN",
        "official_topology_public_constraints": reports.get("official_topology_constraints", {}).get("status", "MISSING"),
    }
    status = "FAIL" if hard_fail else "PASS_WITH_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
    report = {
        "schema": "boqsc.transvoxel.strict_correctness_audit.v1",
        "status": status,
        "transvoxel_style_proof": "PASS" if not hard_fail else "FAIL",
        "official_transvoxel_equivalence_proof": "NOT_PROVEN",
        "steps": steps,
        "matrix": matrix,
        "reports": reports,
        "meaning": (
            "This is an honesty gate. It proves the published M4 reference "
            "convention when M18 evidence passes while keeping official "
            "73-class numeric mapping and transition topology equivalence "
            "explicitly not proven."
        ),
    }
    (VALIDATION / "strict_correctness_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Strict Correctness Audit",
        "",
        f"Status: **{status}**",
        "",
        f"Transvoxel-style proof: **{report['transvoxel_style_proof']}**",
        f"Official Transvoxel equivalence proof: **{report['official_transvoxel_equivalence_proof']}**",
        "",
        "## Matrix",
        "",
    ]
    for k, v in matrix.items():
        lines.append(f"- `{k}`: **{v}**")
    lines += ["", "## Meaning", "", str(report["meaning"]), ""]
    (VALIDATION / "strict_correctness_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print("strict correctness audit:", status)
    return 0 if not hard_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
