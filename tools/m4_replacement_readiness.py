#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build the machine-readable M4 replacement-readiness decision gate.

This report separates:

1. optional M4 transition-backend runtime readiness;
2. readiness to make M4 the default transition backend;
3. readiness to claim a functional clean-room Transvoxel.cpp replacement;
4. readiness to claim exact table/encoding/byte compatibility.

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
PUBLISHED_TOPOLOGY_REPORT = (
    ROOT / "validation" / "published_transition_topology_report.json"
)
REGULAR_EQUIVALENCE_REPORT = (
    ROOT / "validation" / "regular_cell_equivalence_report.json"
)
CONSUMER_COMPATIBILITY_REPORT = (
    ROOT / "validation" / "consumer_compatibility_report.json"
)
EXACT_CLAIM_BOUNDARY_REPORT = (
    ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
)
OFFICIAL_ORACLE_REPORT = (
    ROOT / "validation" / "official_oracle_comparison_report.json"
)
M24_EXACT_TOPOLOGY_REPORT = (
    ROOT / "validation" / "m24_exact_topology_report.json"
)
M15_REPORT = ROOT / "research" / "official_topology" / "m15" / "m15_report.json"
M15_EXPECTED_STATUS = (
    "PASS_M15_M4_SIX_FACE_ORIENTATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
)
M16_REPORT = ROOT / "research" / "official_topology" / "m16" / "m16_report.json"
M16_EXPECTED_STATUS = (
    "PASS_M16_M4_DEFORMED_CORNER_JUNCTIONS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
)
M17_REPORT = ROOT / "research" / "official_topology" / "m17" / "m17_report.json"
M17_EXPECTED_STATUS = (
    "PASS_M17_M4_SELECTED_PRODUCTION_GATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
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
    published_topology = (
        read_json(PUBLISHED_TOPOLOGY_REPORT)
        if PUBLISHED_TOPOLOGY_REPORT.exists()
        else {}
    )
    regular_equivalence = (
        read_json(REGULAR_EQUIVALENCE_REPORT)
        if REGULAR_EQUIVALENCE_REPORT.exists()
        else {}
    )
    consumer_compatibility = (
        read_json(CONSUMER_COMPATIBILITY_REPORT)
        if CONSUMER_COMPATIBILITY_REPORT.exists()
        else {}
    )
    exact_claim_boundary = (
        read_json(EXACT_CLAIM_BOUNDARY_REPORT)
        if EXACT_CLAIM_BOUNDARY_REPORT.exists()
        else {}
    )
    official_oracle = (
        read_json(OFFICIAL_ORACLE_REPORT)
        if OFFICIAL_ORACLE_REPORT.exists()
        else {}
    )
    m24_exact_topology = (
        read_json(M24_EXACT_TOPOLOGY_REPORT)
        if M24_EXACT_TOPOLOGY_REPORT.exists()
        else {}
    )
    if M15_REPORT.exists():
        try:
            m15_status = str(
                read_json(M15_REPORT).get("status", "MISSING_STATUS")
            )
        except Exception:
            m15_status = "INVALID_JSON"
    else:
        m15_status = "MISSING"
    if M16_REPORT.exists():
        try:
            m16_status = str(
                read_json(M16_REPORT).get("status", "MISSING_STATUS")
            )
        except Exception:
            m16_status = "INVALID_JSON"
    else:
        m16_status = "MISSING"
    if M17_REPORT.exists():
        try:
            m17_status = str(
                read_json(M17_REPORT).get("status", "MISSING_STATUS")
            )
        except Exception:
            m17_status = "INVALID_JSON"
    else:
        m17_status = "MISSING"

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
            "PASS" if m16_status == M16_EXPECTED_STATUS else "BLOCKED",
            [
                rel(M16_REPORT),
                "validation/m4_corner_junction_report.json",
            ],
            m16_status,
            M16_EXPECTED_STATUS,
            (
                "M16: validate mapped non-box M4 cells where three perpendicular "
                "LOD transition faces meet."
                if m16_status != M16_EXPECTED_STATUS
                else None
            ),
        ),
        gate(
            "m4_selected_full_production_gate",
            "Full production gate with M4 installed through the normal backend API",
            "default_replacement",
            ["default_transition_backend", "functional_full_replacement"],
            "PASS" if m17_status == M17_EXPECTED_STATUS else "BLOCKED",
            [
                rel(M17_REPORT),
                "proof/m4_production_gate.json",
            ],
            m17_status,
            M17_EXPECTED_STATUS,
            (
                "M17: run the complete production assembler/gate with M4 "
                "explicitly installed."
                if m17_status != M17_EXPECTED_STATUS
                else None
            ),
        ),
        gate(
            "official_reference_convention_equivalence",
            "Published sign, sample-order, face-frame, winding, and orientation convention equivalence",
            "official_equivalence",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            (
                "PASS"
                if reference.get("official_reference_equivalence") == "PROVEN"
                else "BLOCKED"
            ),
            [
                rel(reference_path),
                "validation/reference_convention_report.json",
                "research/official_topology/m18/m18_report.json",
            ],
            reference.get("official_reference_equivalence", "MISSING"),
            "PROVEN",
            (
                "Derive a no-copy reference transform specification and prove "
                "all transition orientations against it."
                if reference.get("official_reference_equivalence") != "PROVEN"
                else None
            ),
            (
                "This gate covers the published algorithmic convention through "
                "an explicit case-index bijection. Exact table encoding remains "
                "tracked separately."
            ),
        ),
        gate(
            "official_transition_topology_equivalence",
            "Published transition topology behavior for all 512 cases",
            "official_equivalence",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            (
                "PASS"
                if published_topology.get(
                    "published_transition_topology_behavior"
                )
                == "PROVEN"
                else "BLOCKED"
            ),
            [
                rel(PUBLISHED_TOPOLOGY_REPORT),
                rel(m3_triangles_path),
                "research/official_topology/m19/m19_report.json",
            ],
            published_topology.get(
                "published_transition_topology_behavior",
                "MISSING",
            ),
            "PROVEN",
            (
                "Prove the clean-room face contours, D4/inversion classes, "
                "and minimal manifold fillings satisfy the published "
                "algorithmic topology."
                if published_topology.get(
                    "published_transition_topology_behavior"
                )
                != "PROVEN"
                else None
            ),
            (
                "Functional behavior does not require identical official "
                "interior diagonals; exact triangulation identity is tracked "
                "separately."
            ),
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
            "official_triangle_triangulation_identity",
            "Exact official transition interior triangulation identity",
            "table_compatibility",
            ["exact_table_compatible_replacement"],
            (
                "PASS"
                if m24_exact_topology.get("status")
                == "PASS_M24_EXACT_REGULAR_TRANSITION_TOPOLOGY"
                and m24_exact_topology.get("decisions", {}).get(
                    "exact_topology_identity"
                )
                is True
                else "BLOCKED"
            ),
            [
                rel(m3_triangles_path),
                (
                    rel(M24_EXACT_TOPOLOGY_REPORT)
                    if M24_EXACT_TOPOLOGY_REPORT.exists()
                    else "validation/m24_exact_topology_report.json"
                ),
            ],
            (
                "PROVEN"
                if m24_exact_topology.get("decisions", {}).get(
                    "exact_topology_identity"
                )
                is True
                else triangles.get(
                    "official_triangle_topology_equivalence",
                    "MISSING",
                )
            ),
            "PROVEN",
            (
                "Run M24 to select exact topology from independently enumerated "
                "clean-room boundary-loop triangulations."
                if m24_exact_topology.get("decisions", {}).get(
                    "exact_topology_identity"
                )
                is not True
                else None
            ),
            (
                "M24 proves exact regular and transition edge-labeled oriented "
                "topology. Packed encodings and table layout remain separate."
            ),
        ),
        gate(
            "official_regular_cell_equivalence",
            "Clean-room modified-Marching-Cubes regular-cell behavior",
            "full_replacement",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            (
                "PASS"
                if regular_equivalence.get(
                    "functional_regular_cell_equivalence"
                )
                == "PROVEN"
                else "BLOCKED"
            ),
            [
                rel(REGULAR_EQUIVALENCE_REPORT),
                "research/official_topology/m20/m20_report.json",
                "generated/regular_tables.json",
            ],
            regular_equivalence.get(
                "functional_regular_cell_equivalence",
                "MISSING",
            ),
            "PROVEN",
            (
                "Derive and validate preferred-polarity regular-cell topology "
                "with exhaustive regular/regular and regular/M4 seam proof."
                if regular_equivalence.get(
                    "functional_regular_cell_equivalence"
                )
                != "PROVEN"
                else None
            ),
            (
                "Functional behavior is separate from exact official regular "
                "class numbers, reuse codes, and table bytes."
            ),
        ),
        gate(
            "official_regular_table_identity",
            "Exact official regular-cell class/encoding/table identity",
            "table_compatibility",
            ["exact_table_compatible_replacement"],
            "BLOCKED",
            [rel(REGULAR_EQUIVALENCE_REPORT)],
            "NOT_PROVEN",
            "PROVEN",
            (
                "Do not use official arrays as an oracle. Exact regular table "
                "identity is not required for functional replacement."
            ),
        ),
        gate(
            "transvoxel_cpp_consumer_compatibility_contract",
            "Documented and tested compatibility contract for Transvoxel.cpp consumers",
            "full_replacement",
            ["functional_full_replacement", "exact_table_compatible_replacement"],
            (
                "PASS"
                if consumer_compatibility.get(
                    "functional_transvoxel_cpp_consumer_compatibility"
                )
                == "PROVEN"
                and consumer_compatibility.get("status")
                == "PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY"
                else "BLOCKED"
            ),
            [
                rel(CONSUMER_COMPATIBILITY_REPORT)
                if CONSUMER_COMPATIBILITY_REPORT.exists()
                else "validation/consumer_compatibility_report.json",
                "examples/c_m21_consumer_contract/main.c",
                "examples/cpp_consumer/main.cpp",
            ],
            consumer_compatibility.get(
                "functional_transvoxel_cpp_consumer_compatibility",
                "MISSING",
            ),
            "PROVEN",
            (
                "Run tools/test_consumer_compatibility.py to compile and test "
                "the public C and C++ consumer contract."
                if consumer_compatibility.get(
                    "functional_transvoxel_cpp_consumer_compatibility"
                )
                != "PROVEN"
                else None
            ),
            (
                "This gate proves the behavioral public API replacement "
                "contract. It does not claim field-for-field or byte-for-byte "
                "Transvoxel.cpp table compatibility."
            ),
        ),
        gate(
            "exact_0bsd_provenance_clearance",
            "0BSD provenance clearance for oracle-calibrated exact data",
            "provenance",
            ["exact_table_compatible_replacement"],
            "BLOCKED",
            [
                (
                    rel(M24_EXACT_TOPOLOGY_REPORT)
                    if M24_EXACT_TOPOLOGY_REPORT.exists()
                    else "validation/m24_exact_topology_report.json"
                ),
                "docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md",
            ],
            m24_exact_topology.get("decisions", {}).get(
                "exact_0bsd_provenance_cleared",
                False,
            ),
            True,
            (
                "Replace oracle-calibrated selections with a defensible "
                "independent derivation or obtain explicit provenance/legal "
                "clearance before shipping them as 0BSD."
            ),
            (
                "M24 is research-only until this gate passes. The existing "
                "independent functional core remains 0BSD."
            ),
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
        "official_triangle_triangulation_identity",
        "official_regular_table_identity",
        "exact_0bsd_provenance_clearance",
        "official_transvoxel_cpp_byte_identity",
    }

    status_by_id = {item["id"]: item["status"] for item in gates}
    default_ready = runtime_pass and all(status_by_id.get(gate_id) == "PASS" for gate_id in default_required)
    functional_ready = all(status_by_id.get(gate_id) == "PASS" for gate_id in functional_required)
    exact_ready = all(status_by_id.get(gate_id) == "PASS" for gate_id in exact_required)
    passing_ids = [item["id"] for item in gates if item["status"] == "PASS"]
    blocking_ids = [item["id"] for item in gates if item["status"] == "BLOCKED"]
    failed_ids = [item["id"] for item in gates if item["status"] == "FAIL"]

    analysis_ok = (
        not load_errors
        and not failed_ids
        and runtime_pass
    )
    reference_proven = (
        reference.get("official_reference_equivalence") == "PROVEN"
    )
    topology_proven = (
        published_topology.get("published_transition_topology_behavior")
        == "PROVEN"
    )
    regular_proven = (
        regular_equivalence.get("functional_regular_cell_equivalence")
        == "PROVEN"
    )
    claim_boundary_documented = (
        exact_claim_boundary.get("status")
        == "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"
    )
    if functional_ready:
        if claim_boundary_documented:
            if (
                m24_exact_topology.get("status")
                == "PASS_M24_EXACT_REGULAR_TRANSITION_TOPOLOGY"
                and m24_exact_topology.get("decisions", {}).get(
                    "exact_topology_identity"
                )
                is True
            ):
                next_milestone = {
                    "id": "M25_EXACT_VERTEX_ENCODING_AND_TABLE_LAYOUT",
                    "objective": (
                        "Derive official-compatible vertex order/reuse "
                        "encodings and class/table layout, then expose an "
                        "unchanged-consumer compatibility surface."
                    ),
                    "why_first": (
                        "M24 reaches exact oriented topology for every regular "
                        "and transition case. The remaining exact blockers are "
                        "class IDs, packed vertex/reuse encoding, regular table "
                        "layout, and unchanged-consumer/file compatibility."
                    ),
                }
            elif (
                official_oracle.get("status")
                == "PASS_M23_OFFICIAL_ORACLE_BASELINE_EXACT_REPLACEMENT_NOT_READY"
                and official_oracle.get("decisions", {}).get(
                    "oracle_baseline_complete"
                )
                is True
            ):
                next_milestone = {
                    "id": "M24_EXACT_TOPOLOGY_CONVERGENCE",
                    "objective": (
                        "Converge all 256 regular and 512 transition cases on "
                        "the verified official edge-labeled oriented topology."
                    ),
                    "why_first": (
                        "M23 measured the exact gaps. Counts and crossing-edge "
                        "sets already match, while regular and transition "
                        "triangulation choices still differ in many cases."
                    ),
                }
            else:
                next_milestone = {
                    "id": "M23_OFFICIAL_ORACLE_BASELINE",
                    "objective": (
                        "Compare every regular and transition case with a "
                        "verified external official Transvoxel.cpp oracle."
                    ),
                    "why_first": (
                        "Exact replacement is the intended finish line. A "
                        "measured exhaustive baseline is required before "
                        "changing topology, encoding, or compatibility surfaces."
                    ),
                }
        else:
            next_milestone = {
                "id": "M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY",
                "objective": (
                    "Keep functional replacement evidence green while deciding "
                    "whether exact table-layout/class-ID/encoding compatibility is "
                    "a required product goal."
                ),
                "why_first": (
                    "M21 makes the public C/C++ functional replacement ready. The "
                    "remaining blockers are exact official compatibility claims, "
                    "not functional behavior blockers."
                ),
            }
    elif (
        m15_status == M15_EXPECTED_STATUS
        and m16_status == M16_EXPECTED_STATUS
        and m17_status == M17_EXPECTED_STATUS
        and reference_proven
        and topology_proven
        and regular_proven
    ):
        next_milestone = {
            "id": "M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY",
            "objective": (
                "Define and test the functional compatibility contract for "
                "Transvoxel.cpp consumers, then select the clean-room M4 "
                "transition path by default."
            ),
            "why_first": (
                "Transition and regular-cell functional behavior now pass. "
                "The remaining functional replacement blocker is the consumer "
                "compatibility/default-selection contract."
            ),
        }
    elif (
        m15_status == M15_EXPECTED_STATUS
        and m16_status == M16_EXPECTED_STATUS
        and m17_status == M17_EXPECTED_STATUS
        and reference_proven
        and topology_proven
    ):
        next_milestone = {
            "id": "M20_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE",
            "objective": (
                "Prove clean-room regular-cell topology/reference behavior "
                "needed for a functional full Transvoxel.cpp replacement."
            ),
            "why_first": (
                "Transition production, reference convention, and published "
                "transition topology behavior now pass. Regular-cell behavior "
                "is the next implementation blocker to a functional full "
                "replacement."
            ),
        }
    elif (
        m15_status == M15_EXPECTED_STATUS
        and m16_status == M16_EXPECTED_STATUS
        and m17_status == M17_EXPECTED_STATUS
        and reference_proven
    ):
        next_milestone = {
            "id": "M19_OFFICIAL_TRANSITION_TOPOLOGY_VALIDATION",
            "objective": (
                "Prove the independently derived transition triangulation "
                "topology satisfies the published Transvoxel topology rules "
                "for all 512 cases without reading official lookup arrays."
            ),
            "why_first": (
                "The default-backend production gate and published reference "
                "convention now pass. Transition topology is the next "
                "algorithmic blocker to a functional full replacement claim."
            ),
        }
    elif (
        m15_status == M15_EXPECTED_STATUS
        and m16_status == M16_EXPECTED_STATUS
        and m17_status == M17_EXPECTED_STATUS
    ):
        next_milestone = {
            "id": "M18_OFFICIAL_REFERENCE_CONVENTION_VALIDATION",
            "objective": (
                "Derive and prove the official sign, sample-order, face-frame, "
                "winding, and orientation convention without reading official "
                "lookup-table arrays."
            ),
            "why_first": (
                "The M4 candidate now passes every default-backend runtime and "
                "production gate. Reference-convention equivalence is the next "
                "algorithmic blocker to a functional full replacement claim."
            ),
        }
    elif (
        m15_status == M15_EXPECTED_STATUS
        and m16_status == M16_EXPECTED_STATUS
    ):
        next_milestone = {
            "id": "M17_M4_SELECTED_PRODUCTION_GATE",
            "objective": (
                "Run the complete production proof path with M4 explicitly "
                "installed through the normal backend API and mapped transition "
                "geometry enabled."
            ),
            "why_first": (
                "Six-face orientation and mapped corner junctions now pass. The "
                "remaining self-contained default-replacement blocker is a full "
                "production run with M4 selected end to end."
            ),
        }
    elif m15_status == M15_EXPECTED_STATUS:
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

    if not analysis_ok:
        readiness_status = "FAIL_M4_REPLACEMENT_READINESS_ANALYSIS"
    elif exact_ready:
        readiness_status = "READY_EXACT_TABLE_COMPATIBLE_TRANSVOXEL_CPP_REPLACEMENT"
    elif functional_ready:
        readiness_status = (
            "READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_"
            "EXACT_COMPATIBILITY_BLOCKED"
        )
    elif default_ready:
        readiness_status = (
            "READY_M4_DEFAULT_TRANSITION_BACKEND_FUNCTIONAL_FULL_REPLACEMENT_BLOCKED"
        )
    else:
        readiness_status = "BLOCKED_M4_DEFAULT_REPLACEMENT_REQUIRED_EVIDENCE_NOT_PROVEN"

    if functional_ready and not exact_ready:
        meaning = (
            "The public clean-room C/C++ API is ready to use as a functional "
            "Transvoxel.cpp replacement: default regular cells, default M4 "
            "transition cells, published behavior proofs, and consumer "
            "compile/link tests pass. Exact official table layout, class IDs, "
            "vertex encoding, triangulation identity, and byte identity remain "
            "separate blocked claims."
        )
    elif exact_ready:
        meaning = "Exact table-compatible replacement is marked ready."
    elif default_ready:
        if reference_proven and topology_proven and not regular_proven:
            meaning = (
                "M4 now passes the default-transition-backend production, "
                "published reference-convention, and published transition-"
                "topology behavior gates, but a functional full Transvoxel.cpp "
                "replacement remains blocked on regular-cell equivalence and "
                "consumer compatibility."
            )
        elif reference_proven and topology_proven and regular_proven:
            meaning = (
                "M4 and the clean-room regular core now pass all functional "
                "geometry gates, but a full Transvoxel.cpp replacement remains "
                "blocked on the consumer compatibility and default-selection "
                "contract."
            )
        else:
            meaning = (
                "M4 now passes the explicit default-transition-backend runtime "
                "and production gates, but a functional full Transvoxel.cpp "
                "replacement remains blocked on published behavior, regular-"
                "cell equivalence, and consumer compatibility."
            )
    else:
        meaning = (
            "The optional M4 transition backend has strong runtime/integration "
            "evidence, but it is not ready to replace the default backend and "
            "is not a proven full Transvoxel.cpp replacement."
        )

    if functional_ready:
        claim_allowed = (
            "Functional clean-room Transvoxel.cpp replacement through the "
            "public C/C++ API: default regular and transition builders use "
            "clean-room published behavior; C and C++ consumers can "
            "compile/link; callback customization is retained."
        )
        claim_not_allowed = (
            "Exact official Transvoxel.cpp table layout, class-ID, vertex "
            "encoding, triangulation-identity, or byte-identity claim."
        )
    elif default_ready:
        claim_allowed = (
            "Clean-room M4 transition backend with enough runtime and "
            "production evidence to replace the independent default transition "
            "backend."
        )
        claim_not_allowed = "Exact official topology/table/byte equivalence claim."
    else:
        claim_allowed = (
            "Optional clean-room M4 transition-backend candidate with passing "
            "runtime/integration milestones."
        )
        claim_not_allowed = (
            "Proven full Transvoxel.cpp replacement, official topology "
            "equivalence, or default backend replacement."
        )

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_replacement_readiness.v1",
        "status": readiness_status,
        "analysis_completed": analysis_ok,
        "meaning": meaning,
        "decisions": {
            "optional_transition_backend_candidate_ready": runtime_pass,
            "ready_to_replace_default_transition_backend": default_ready,
            "functional_full_replacement_ready": functional_ready,
            "exact_table_compatible_replacement_ready": exact_ready,
            "exact_compatibility_claim_boundary_documented": claim_boundary_documented,
        },
        "load_errors": load_errors,
        "passing_gate_ids": passing_ids,
        "blocking_gate_ids": blocking_ids,
        "failed_gate_ids": failed_ids,
        "gates": gates,
        "next_milestone": next_milestone,
        "claim_boundary": {
            "allowed_now": claim_allowed,
            "not_allowed_now": claim_not_allowed,
            "byte_identity_required_for_functional_replacement": False,
            "byte_identity_required_for_exact_table_identity_claim": True,
            "m22_claim_boundary_report": (
                rel(EXACT_CLAIM_BOUNDARY_REPORT)
                if EXACT_CLAIM_BOUNDARY_REPORT.exists()
                else "validation/exact_compatibility_claim_boundary_report.json"
            ),
            "m23_official_oracle_report": (
                rel(OFFICIAL_ORACLE_REPORT)
                if OFFICIAL_ORACLE_REPORT.exists()
                else "validation/official_oracle_comparison_report.json"
            ),
            "m24_exact_topology_report": (
                rel(M24_EXACT_TOPOLOGY_REPORT)
                if M24_EXACT_TOPOLOGY_REPORT.exists()
                else "validation/m24_exact_topology_report.json"
            ),
            "exact_replacement_finish_line": (
                "Field/output/symbol compatibility sufficient for unchanged "
                "consumer integration. Byte-identical source text is not "
                "required."
            ),
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report)
    print("M4 replacement readiness:", report["status"])
    print("optional backend candidate ready:", runtime_pass)
    print("default replacement ready:", default_ready)
    print("functional full replacement ready:", functional_ready)
    print("exact claim boundary documented:", claim_boundary_documented)
    print("blocking gates:", len(blocking_ids))
    print("next milestone:", report["next_milestone"]["id"])
    return 0 if analysis_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
