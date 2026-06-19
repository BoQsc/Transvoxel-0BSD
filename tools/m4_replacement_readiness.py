#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build the machine-readable M4 replacement-readiness decision gate.

This report separates:

1. optional M4 transition-backend runtime readiness;
2. readiness to make M4 the default transition backend;
3. readiness to claim a full clean-room Transvoxel.cpp replacement.

A blocked replacement decision is an expected successful analysis result. The
tool returns nonzero only when required evidence files are missing/malformed or
the accumulated M4 runtime milestones have regressed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "validation" / "m4_replacement_readiness_report.json"
REPORT_MD = ROOT / "validation" / "m4_replacement_readiness_report.md"
M15_REPORT = ROOT / "research" / "official_topology" / "m15" / "m15_report.json"
M15_EXPECTED_STATUS = (
    "PASS_M15_M4_SIX_FACE_ORIENTATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
)

MILESTONES = {
    "m4_runtime_tables": (
        ROOT / "research" / "official_topology" / "m4" / "m4_report.json",
        "PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m5_c_runtime": (
        ROOT / "research" / "official_topology" / "m5" / "m5_report.json",
        "PASS_M5_OPT_IN_C_RUNTIME_CANDIDATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m6_c_seams": (
        ROOT / "research" / "official_topology" / "m6" / "m6_report.json",
        "PASS_M6_M4_C_SEAM_VALIDATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m7_normal_api": (
        ROOT / "research" / "official_topology" / "m7" / "m7_report.json",
        "PASS_M7_NORMAL_API_M4_BACKEND_SWITCH_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m8_package": (
        ROOT / "research" / "official_topology" / "m8" / "m8_report.json",
        "PASS_M8_M4_BACKEND_PACKAGE_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m9_terrain_export": (
        ROOT / "research" / "official_topology" / "m9" / "m9_report.json",
        "PASS_M9_M4_TERRAIN_EXPORT_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m10_godot_metrics": (
        ROOT / "research" / "official_topology" / "m10" / "m10_report.json",
        "PASS_M10_M4_GODOT_DATA_PATH_METRICS_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m11_godot_viewer": (
        ROOT / "research" / "official_topology" / "m11" / "m11_report.json",
        "PASS_M11_M4_GODOT_VIEWER_EXPORT_PATH_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m12_backend_compare": (
        ROOT / "research" / "official_topology" / "m12" / "m12_report.json",
        "PASS_M12_M4_GODOT_BACKEND_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
    "m13_scripted_edits": (
        ROOT / "research" / "official_topology" / "m13" / "m13_report.json",
        "PASS_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
    ),
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def gate(
    gate_id: str,
    title: str,
    category: str,
    required_for: List[str],
    status: str,
    evidence: List[str],
    actual: Any,
    expected: Any,
    next_action: str | None = None,
    note: str | None = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "id": gate_id,
        "title": title,
        "category": category,
        "required_for": required_for,
        "status": status,
        "evidence": evidence,
        "actual": actual,
        "expected": expected,
    }
    if next_action:
        result["next_action"] = next_action
    if note:
        result["note"] = note
    return result


def write_markdown(report: Dict[str, Any]) -> None:
    lines = [
        "# M4 Replacement Readiness",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Decisions",
        "",
        f"- Optional M4 transition backend candidate ready: `{report['decisions']['optional_transition_backend_candidate_ready']}`",
        f"- Ready to replace the default transition backend: `{report['decisions']['ready_to_replace_default_transition_backend']}`",
        f"- Ready to claim a functional full Transvoxel.cpp replacement: `{report['decisions']['functional_full_replacement_ready']}`",
        f"- Ready to claim exact table/encoding compatibility: `{report['decisions']['exact_table_compatible_replacement_ready']}`",
        "",
        "## Passing evidence",
        "",
    ]
    for item in report["passing_gate_ids"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocking evidence", ""])
    for gate_data in report["gates"]:
        if gate_data["status"] == "BLOCKED":
            lines.append(f"- `{gate_data['id']}`: {gate_data['title']}")
            lines.append(f"  - Actual: `{gate_data['actual']}`")
            lines.append(f"  - Required: `{gate_data['expected']}`")
            if gate_data.get("next_action"):
                lines.append(f"  - Next: {gate_data['next_action']}")
    lines.extend([
        "",
        "## Next milestone",
        "",
        f"`{report['next_milestone']['id']}` — {report['next_milestone']['objective']}",
        "",
        "Byte-for-byte table identity is tracked separately. It is not required for a functional clean-room replacement, but it is required before claiming exact table-file compatibility.",
        "",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    gates: List[Dict[str, Any]] = []
    load_errors: List[str] = []
    milestone_data: Dict[str, Dict[str, Any]] = {}

    for gate_id, (path, expected_status) in MILESTONES.items():
        if not path.exists():
            load_errors.append("missing " + rel(path))
            actual_status = "MISSING"
            data: Dict[str, Any] = {}
        else:
            try:
                data = read_json(path)
                actual_status = str(data.get("status", "MISSING_STATUS"))
            except Exception as exc:
                load_errors.append(f"invalid {rel(path)}: {exc!r}")
                actual_status = "INVALID_JSON"
                data = {}
        milestone_data[gate_id] = data
        gates.append(gate(
            gate_id,
            title=gate_id.replace("_", " "),
            category="candidate_runtime",
            required_for=["optional_transition_backend", "default_transition_backend", "functional_full_replacement"],
            status="PASS" if actual_status == expected_status else "FAIL",
            evidence=[rel(path)],
            actual=actual_status,
            expected=expected_status,
            next_action="Rerun or repair the regressed M4 milestone." if actual_status != expected_status else None,
        ))

    m3_partition_path = ROOT / "research" / "official_topology" / "m3" / "class_partition.json"
    m3_triangles_path = ROOT / "research" / "official_topology" / "m3" / "candidate_triangulations.json"
    reference_path = ROOT / "validation" / "reference_convention_matrix.json"
    partition = read_json(m3_partition_path)
    triangles = read_json(m3_triangles_path)
    reference = read_json(reference_path)
    if M15_REPORT.exists():
        try:
            m15_status = str(
                read_json(M15_REPORT).get("status", "MISSING_STATUS")
            )
        except Exception:
            m15_status = "INVALID_JSON"
    else:
        m15_status = "MISSING"

    gates.extend([
        gate(
            "m4_all_six_face_orientation_runtime_validation",
            "M4 runtime proof across all +/-X, +/-Y, +/-Z transition-face orientations",
            "default_replacement",
            ["default_transition_backend", "functional_full_replacement"],
            "PASS" if m15_status == M15_EXPECTED_STATUS else "BLOCKED",
            [
                rel(M15_REPORT),
                "validation/m4_six_face_orientation_report.json",
            ],
            m15_status,
            M15_EXPECTED_STATUS,
            (
                "M15: transform M4 sample/vertex frames through all six face "
                "orientations and validate C/Godot mesh output."
                if m15_status != M15_EXPECTED_STATUS
                else None
            ),
        ),
        gate(
            "m4_multi_face_corner_junction_validation",
            "M4-selected corner and multi-neighbor LOD junction proof",
            "default_replacement",
            ["default_transition_backend", "functional_full_replacement"],
            "BLOCKED",
            ["validation/corner_junction_report.json covers the independent default core, not M4-selected junctions."],
            "MISSING_M4_SELECTED_JUNCTION_EVIDENCE",
            "PASS M4-specific corner/junction report",
            "After six-face orientation proof, assemble and validate M4 multi-face corner junctions.",
        ),
        gate(
            "m4_selected_full_production_gate",
            "Full production gate with M4 installed through the normal backend API",
            "default_replacement",
            ["default_transition_backend", "functional_full_replacement"],
            "BLOCKED",
            ["proof/production_gate.json currently proves the independent default backend.", "No proof/m4_production_gate.json exists."],
            "MISSING_M4_PRODUCTION_GATE",
            "PASS M4-selected runtime, mesh, six-face seams, scripted edits, and production gate",
            "Run the complete production assembler/gate with M4 explicitly installed after orientation and junction validation.",
        ),
        gate(
            "official_reference_convention_equivalence",
            "Official sign, sample-order, face-frame, winding, and orientation convention equivalence",
            "official_equivalence",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            "BLOCKED",
            [rel(reference_path)],
            reference.get("official_reference_equivalence", "MISSING"),
            "PROVEN",
            "Derive a no-copy reference transform specification and prove all transition orientations against it.",
        ),
        gate(
            "official_transition_topology_equivalence",
            "Official transition triangulation/topology equivalence for all 512 cases",
            "official_equivalence",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            "BLOCKED",
            [rel(m3_triangles_path)],
            triangles.get("official_triangle_topology_equivalence", "MISSING"),
            "PROVEN",
            "Prove the independently derived ambiguity resolutions and triangle topology match the published algorithmic topology.",
        ),
        gate(
            "official_class_id_mapping",
            "Official 73 transition-class mapping",
            "table_compatibility",
            ["exact_table_compatible_replacement"],
            "BLOCKED",
            [rel(m3_partition_path)],
            partition.get("official_class_id_mapping", "MISSING"),
            "PROVEN",
            "Derive official-compatible class numbering from a no-copy canonical representative ordering.",
        ),
        gate(
            "official_vertex_encoding_equivalence",
            "Official transition vertex encoding and reuse metadata equivalence",
            "table_compatibility",
            ["exact_table_compatible_replacement"],
            "BLOCKED",
            [rel(m3_triangles_path)],
            triangles.get("official_vertex_encoding_equivalence", "MISSING"),
            "PROVEN",
            "Define and prove an independently derived vertex-code/cache-reuse encoding contract.",
        ),
        gate(
            "official_regular_cell_equivalence",
            "Official regular-cell topology/reference behavior for a full Transvoxel.cpp replacement",
            "full_replacement",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            "BLOCKED",
            ["M4 currently supplies only an official-topology transition candidate.", "No official regular-cell candidate/report exists."],
            "MISSING_OFFICIAL_REGULAR_CELL_CANDIDATE",
            "Proven clean-room regular-cell topology/reference behavior",
            "Create a separate no-copy regular-cell equivalence track after the transition orientation gate is established.",
        ),
        gate(
            "transvoxel_cpp_consumer_compatibility_contract",
            "Documented and tested compatibility contract for Transvoxel.cpp consumers",
            "full_replacement",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            "BLOCKED",
            ["The current public product is a plain C API and does not claim field-for-field Transvoxel.cpp consumer compatibility."],
            "NOT_CLAIMED",
            "Explicit adapter/compatibility contract with compile and behavior tests",
            "Specify whether the final product is behavioral replacement, source adapter, or table-layout compatible, then test that contract.",
        ),
        gate(
            "official_transvoxel_cpp_byte_identity",
            "Byte-for-byte identity with the MIT Transvoxel.cpp table file",
            "informational",
            ["exact_table_compatible_replacement"],
            "BLOCKED",
            [rel(MILESTONES["m13_scripted_edits"][0])],
            milestone_data["m13_scripted_edits"].get("official_transvoxel_cpp_byte_identity", "MISSING"),
            "PROVEN only if exact table-file compatibility is claimed",
            "Do not use official arrays as an oracle. This is not required for a functional clean-room replacement.",
            "Not a blocker for functional replacement; it blocks only an exact table-file identity claim.",
        ),
    ])

    runtime_gate_ids = list(MILESTONES)
    runtime_pass = all(
        next(item for item in gates if item["id"] == gate_id)["status"] == "PASS"
        for gate_id in runtime_gate_ids
    )
    default_required = {
        *runtime_gate_ids,
        "m4_all_six_face_orientation_runtime_validation",
        "m4_multi_face_corner_junction_validation",
        "m4_selected_full_production_gate",
    }
    functional_required = {
        *default_required,
        "official_reference_convention_equivalence",
        "official_transition_topology_equivalence",
        "official_regular_cell_equivalence",
        "transvoxel_cpp_consumer_compatibility_contract",
    }
    exact_required = {
        *functional_required,
        "official_class_id_mapping",
        "official_vertex_encoding_equivalence",
        "official_transvoxel_cpp_byte_identity",
    }

    status_by_id = {item["id"]: item["status"] for item in gates}
    default_ready = runtime_pass and all(status_by_id.get(gate_id) == "PASS" for gate_id in default_required)
    functional_ready = all(status_by_id.get(gate_id) == "PASS" for gate_id in functional_required)
    exact_ready = all(status_by_id.get(gate_id) == "PASS" for gate_id in exact_required)
    passing_ids = [item["id"] for item in gates if item["status"] == "PASS"]
    blocking_ids = [item["id"] for item in gates if item["status"] == "BLOCKED"]
    failed_ids = [item["id"] for item in gates if item["status"] == "FAIL"]

    analysis_ok = not load_errors and not failed_ids and runtime_pass and not default_ready and not functional_ready
    if m15_status == M15_EXPECTED_STATUS:
        next_milestone = {
            "id": "M16_M4_MULTI_FACE_CORNER_JUNCTION_VALIDATION",
            "objective": (
                "Assemble M4-selected transition meshes on multiple perpendicular "
                "LOD faces and prove shared-edge/corner closure in C and Godot."
            ),
            "why_first": (
                "Six-face frame transforms are now proven internally. The next "
                "nearest default-replacement blocker is interaction between two "
                "or three simultaneously selected transition faces."
            ),
        }
    else:
        next_milestone = {
            "id": "M15_M4_SIX_FACE_ORIENTATION_VALIDATION",
            "objective": (
                "Prove M4 runtime geometry and seams across all six transition-face "
                "orientations using explicit sample/vertex frame transforms in C and Godot."
            ),
            "why_first": (
                "This is the nearest self-contained blocker to making M4 the default and "
                "creates the orientation machinery required for later official-reference "
                "and corner-junction proofs."
            ),
        }
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_replacement_readiness.v1",
        "status": (
            "BLOCKED_M4_DEFAULT_REPLACEMENT_REQUIRED_EVIDENCE_NOT_PROVEN"
            if analysis_ok else "FAIL_M4_REPLACEMENT_READINESS_ANALYSIS"
        ),
        "analysis_completed": analysis_ok,
        "meaning": (
            "The optional M4 transition backend has strong runtime/integration evidence, "
            "but it is not ready to replace the default backend and is not a proven full "
            "Transvoxel.cpp replacement. A blocked decision is the expected correct result "
            "until every required gate is proven."
        ),
        "decisions": {
            "optional_transition_backend_candidate_ready": runtime_pass,
            "ready_to_replace_default_transition_backend": default_ready,
            "functional_full_replacement_ready": functional_ready,
            "exact_table_compatible_replacement_ready": exact_ready,
        },
        "load_errors": load_errors,
        "passing_gate_ids": passing_ids,
        "blocking_gate_ids": blocking_ids,
        "failed_gate_ids": failed_ids,
        "gates": gates,
        "next_milestone": next_milestone,
        "claim_boundary": {
            "allowed_now": "Optional clean-room M4 transition-backend candidate with passing runtime/integration milestones.",
            "not_allowed_now": "Proven full Transvoxel.cpp replacement, official topology equivalent, or default backend replacement.",
            "byte_identity_required_for_functional_replacement": False,
            "byte_identity_required_for_exact_table_identity_claim": True,
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report)
    print("M4 replacement readiness:", report["status"])
    print("optional backend candidate ready:", runtime_pass)
    print("default replacement ready:", default_ready)
    print("functional full replacement ready:", functional_ready)
    print("blocking gates:", len(blocking_ids))
    print("next milestone:", report["next_milestone"]["id"])
    return 0 if analysis_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
