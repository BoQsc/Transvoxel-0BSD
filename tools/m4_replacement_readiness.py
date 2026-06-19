#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build the machine-readable M4 replacement-readiness decision gate.

This report separates:

1. optional M4 transition-backend runtime readiness;
2. readiness to make M4 the default transition backend;
3. readiness to claim a functional clean-room Transvoxel.cpp replacement;
4. readiness to claim exact table/encoding/byte compatibility.
5. readiness to ship an exact semantic drop-in replacement under 0BSD.

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
M25_COMPATIBLE_LAYOUT_REPORT = (
    ROOT / "validation" / "m25_compatible_layout_report.json"
)
M25_CONSUMER_REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m25"
    / "m25_consumer_validation.json"
)
M26_INTEGRATION_REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m26"
    / "m26_godot_voxel_integration.json"
)
M26_PROVENANCE_REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m26"
    / "m26_provenance_audit.json"
)
M26_FULL_BUILD_REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m26"
    / "m26_full_godot_voxel_build.json"
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
        f"- Exact semantic drop-in integration ready: `{report['decisions']['exact_drop_in_integration_ready']}`",
        f"- Exact semantic drop-in 0BSD release ready: `{report['decisions']['exact_drop_in_0bsd_replacement_ready']}`",
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
    m25_compatible_layout = (
        read_json(M25_COMPATIBLE_LAYOUT_REPORT)
        if M25_COMPATIBLE_LAYOUT_REPORT.exists()
        else {}
    )
    m25_consumer = (
        read_json(M25_CONSUMER_REPORT)
        if M25_CONSUMER_REPORT.exists()
        else {}
    )
    m26_integration = (
        read_json(M26_INTEGRATION_REPORT)
        if M26_INTEGRATION_REPORT.exists()
        else {}
    )
    m26_provenance = (
        read_json(M26_PROVENANCE_REPORT)
        if M26_PROVENANCE_REPORT.exists()
        else {}
    )
    m26_full_build = (
        read_json(M26_FULL_BUILD_REPORT)
        if M26_FULL_BUILD_REPORT.exists()
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
            "Compatible packed vertex encoding and reuse metadata semantics",
            "table_compatibility",
            ["exact_table_compatible_replacement"],
            (
                "PASS"
                if m25_compatible_layout.get("status")
                == "PASS_M25_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT"
                and m25_compatible_layout.get("decisions", {}).get(
                    "packed_vertex_reuse_semantics"
                )
                is True
                else "BLOCKED"
            ),
            [
                rel(m3_triangles_path),
                (
                    rel(M25_COMPATIBLE_LAYOUT_REPORT)
                    if M25_COMPATIBLE_LAYOUT_REPORT.exists()
                    else "validation/m25_compatible_layout_report.json"
                ),
            ],
            (
                "PROVEN"
                if m25_compatible_layout.get("decisions", {}).get(
                    "packed_vertex_reuse_semantics"
                )
                is True
                else triangles.get(
                    "official_vertex_encoding_equivalence",
                    "MISSING",
                )
            ),
            "PROVEN",
            (
                "Run M25 to derive packed reuse codes from regular/transition "
                "cell geometry and validate all case code multisets."
                if m25_compatible_layout.get("decisions", {}).get(
                    "packed_vertex_reuse_semantics"
                )
                is not True
                else None
            ),
            (
                "M25 proves compatible packed-code semantics. Per-case vertex "
                "order and numeric class IDs may differ internally."
            ),
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
            "compatible_transvoxel_cpp_data_layout",
            "Original Transvoxel.cpp struct/symbol/array-capacity data layout",
            "drop_in_compatibility",
            ["exact_table_compatible_replacement"],
            (
                "PASS"
                if m25_compatible_layout.get("status")
                == "PASS_M25_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT"
                and m25_compatible_layout.get("decisions", {}).get(
                    "compatible_struct_and_symbol_surface"
                )
                is True
                else "BLOCKED"
            ),
            [
                (
                    rel(M25_COMPATIBLE_LAYOUT_REPORT)
                    if M25_COMPATIBLE_LAYOUT_REPORT.exists()
                    else "validation/m25_compatible_layout_report.json"
                ),
                "research/official_topology/m25/generated/Transvoxel.cpp",
            ],
            m25_compatible_layout.get("decisions", {}).get(
                "compatible_struct_and_symbol_surface",
                False,
            ),
            True,
            (
                "Generate the original struct names, global symbols, and "
                "16/56 class-array capacities from M24 topology."
                if m25_compatible_layout.get("decisions", {}).get(
                    "compatible_struct_and_symbol_surface"
                )
                is not True
                else None
            ),
            (
                "Compatible layout does not imply numeric class-ID or byte "
                "identity."
            ),
        ),
        gate(
            "unchanged_style_cpp_consumer",
            "C++ consumer using original Transvoxel.cpp data contract unchanged",
            "drop_in_compatibility",
            ["exact_table_compatible_replacement"],
            (
                "PASS"
                if m25_consumer.get("status")
                == "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER"
                else "BLOCKED"
            ),
            [
                (
                    rel(M25_CONSUMER_REPORT)
                    if M25_CONSUMER_REPORT.exists()
                    else (
                        "research/official_topology/m25/"
                        "m25_consumer_validation.json"
                    )
                ),
                (
                    "research/official_topology/m25/"
                    "original_contract_consumer.cpp"
                ),
            ],
            m25_consumer.get("status", "MISSING"),
            "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER",
            (
                "Compile and run the M25 original-contract C++ consumer."
                if m25_consumer.get("status")
                != "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER"
                else None
            ),
        ),
        gate(
            "godot_voxel_table_integration",
            "Pinned Godot Voxel table-source replacement integration",
            "drop_in_compatibility",
            ["exact_drop_in_replacement"],
            (
                "PASS"
                if m26_integration.get("status")
                == "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION"
                and m26_integration.get("comparison", {}).get(
                    "mismatch_count"
                )
                == 0
                else "BLOCKED"
            ),
            [
                (
                    rel(M26_INTEGRATION_REPORT)
                    if M26_INTEGRATION_REPORT.exists()
                    else (
                        "research/official_topology/m26/"
                        "m26_godot_voxel_integration.json"
                    )
                ),
                (
                    "research/official_topology/m26/"
                    "godot_style_table_consumer.cpp"
                ),
            ],
            m26_integration.get("status", "MISSING"),
            "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION",
            (
                "Compile the actual Godot Voxel table API against the original "
                "and M26 replacement and compare all 781 output records."
                if m26_integration.get("status")
                != "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION"
                else None
            ),
            (
                "This pinned downstream source-contract comparison is "
                "complemented by the separate full GDExtension build gate."
            ),
        ),
        gate(
            "godot_voxel_full_gdextension_build",
            "Full pinned Godot Voxel GDExtension build with replacement table",
            "drop_in_compatibility",
            ["exact_drop_in_replacement"],
            (
                "PASS"
                if m26_full_build.get("status")
                == "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
                else "BLOCKED"
            ),
            [
                (
                    rel(M26_FULL_BUILD_REPORT)
                    if M26_FULL_BUILD_REPORT.exists()
                    else (
                        "research/official_topology/m26/"
                        "m26_full_godot_voxel_build.json"
                    )
                ),
                (
                    "research/official_topology/m26/"
                    "test_full_godot_voxel_build.py"
                ),
            ],
            m26_full_build.get("status", "MISSING"),
            "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD",
            (
                "Build a temporary pinned Godot Voxel clone with the M26 "
                "replacement using Zig and a compatible godot-cpp dependency."
                if m26_full_build.get("status")
                != "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
                else None
            ),
            (
                "The build uses temporary clones only and records artifact "
                "hashes without packaging the DLL."
            ),
        ),
        gate(
            "exact_0bsd_provenance_clearance",
            "0BSD provenance clearance for oracle-calibrated exact data",
            "provenance",
            ["exact_table_compatible_replacement"],
            (
                "PASS"
                if m26_provenance.get("decision", {}).get(
                    "exact_candidate_0bsd_provenance_cleared"
                )
                is True
                else "BLOCKED"
            ),
            [
                (
                    rel(M24_EXACT_TOPOLOGY_REPORT)
                    if M24_EXACT_TOPOLOGY_REPORT.exists()
                    else "validation/m24_exact_topology_report.json"
                ),
                (
                    rel(M26_PROVENANCE_REPORT)
                    if M26_PROVENANCE_REPORT.exists()
                    else (
                        "research/official_topology/m26/"
                        "m26_provenance_audit.json"
                    )
                ),
                "docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md",
            ],
            m26_provenance.get("decision", {}).get(
                "exact_candidate_0bsd_provenance_cleared",
                m24_exact_topology.get("decisions", {}).get(
                    "exact_0bsd_provenance_cleared",
                    False,
                ),
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
        "compatible_transvoxel_cpp_data_layout",
        "unchanged_style_cpp_consumer",
        "exact_0bsd_provenance_clearance",
        "official_transvoxel_cpp_byte_identity",
    }
    drop_in_integration_required = {
        *functional_required,
        "official_vertex_encoding_equivalence",
        "official_triangle_triangulation_identity",
        "compatible_transvoxel_cpp_data_layout",
        "unchanged_style_cpp_consumer",
        "godot_voxel_table_integration",
        "godot_voxel_full_gdextension_build",
    }
    drop_in_release_required = {
        *drop_in_integration_required,
        "exact_0bsd_provenance_clearance",
    }
    identity_only_gate_ids = {
        "official_class_id_mapping",
        "official_regular_table_identity",
        "official_transvoxel_cpp_byte_identity",
    }

    status_by_id = {item["id"]: item["status"] for item in gates}
    default_ready = runtime_pass and all(status_by_id.get(gate_id) == "PASS" for gate_id in default_required)
    functional_ready = all(status_by_id.get(gate_id) == "PASS" for gate_id in functional_required)
    exact_ready = all(status_by_id.get(gate_id) == "PASS" for gate_id in exact_required)
    drop_in_integration_ready = all(
        status_by_id.get(gate_id) == "PASS"
        for gate_id in drop_in_integration_required
    )
    drop_in_release_ready = all(
        status_by_id.get(gate_id) == "PASS"
        for gate_id in drop_in_release_required
    )
    drop_in_blocking_ids = sorted(
        gate_id
        for gate_id in drop_in_release_required
        if status_by_id.get(gate_id) != "PASS"
    )
    identity_only_blocking_ids = sorted(
        gate_id
        for gate_id in identity_only_gate_ids
        if status_by_id.get(gate_id) != "PASS"
    )
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
                m26_integration.get("status")
                == "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION"
                and m26_full_build.get("status")
                == "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
            ):
                next_milestone = {
                    "id": "M27_INDEPENDENT_EXACT_TOPOLOGY_PROVENANCE",
                    "objective": (
                        "Replace the M24 oracle-calibrated triangulation "
                        "selection indexes with an independently justified "
                        "deterministic rule, then re-run all exact and "
                        "downstream integration proofs."
                    ),
                    "why_first": (
                        "M26 proves exact semantic table replacement through "
                        "the pinned Godot Voxel consumer API. The only blocker "
                        "to shipping that exact candidate as 0BSD is provenance; "
                        "numeric class IDs and byte identity are identity-only."
                    ),
                }
            elif (
                m25_compatible_layout.get("status")
                == "PASS_M25_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT"
                and m25_consumer.get("status")
                == "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER"
            ):
                next_milestone = {
                    "id": "M26_REAL_ENGINE_INTEGRATION_AND_PROVENANCE",
                    "objective": (
                        "Replace the MIT table file in a real Transvoxel "
                        "consumer integration, compare runtime output, and "
                        "resolve the exact-candidate 0BSD provenance gate."
                    ),
                    "why_first": (
                        "M25 proves compatible original data symbols, array "
                        "capacities, packed reuse semantics, and unchanged-style "
                        "C++ consumption. The remaining practical proof is a "
                        "real engine integration; release remains blocked on "
                        "provenance and identity-only claims."
                    ),
                }
            elif (
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
    elif drop_in_release_ready:
        readiness_status = "READY_EXACT_DROP_IN_0BSD_TRANSVOXEL_CPP_REPLACEMENT"
    elif drop_in_integration_ready:
        readiness_status = (
            "READY_EXACT_DROP_IN_INTEGRATION_PROVEN_"
            "0BSD_PROVENANCE_BLOCKED"
        )
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

    if drop_in_release_ready:
        meaning = (
            "The exact semantic Transvoxel.cpp replacement passes the "
            "downstream source-contract integration and its generated data is "
            "cleared for 0BSD release. Numeric class IDs and source bytes remain "
            "separate identity-only claims."
        )
    elif drop_in_integration_ready:
        meaning = (
            "The research candidate is an exact semantic drop-in replacement "
            "through the pinned Godot Voxel table API: all 256 regular cases, "
            "512 transition cases, packed reuse records, winding, and corner "
            "reuse records match, and the full Windows GDExtension compiles "
            "and links with Zig. It cannot yet ship as 0BSD because M24 "
            "triangulation selections are oracle-calibrated."
        )
    elif functional_ready and not exact_ready:
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
        if drop_in_integration_ready:
            claim_allowed = (
                "Functional clean-room Transvoxel.cpp replacement through the "
                "public C/C++ API, plus a research-only exact semantic "
                "drop-in candidate proven through the pinned Godot Voxel "
                "table API."
            )
            claim_not_allowed = (
                "0BSD release claim for the M24-M26 exact candidate before "
                "provenance clearance; Exact official Transvoxel.cpp numeric "
                "class-ID, table-byte, or source-byte identity claim."
            )
        else:
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
            "exact_drop_in_integration_ready": drop_in_integration_ready,
            "exact_drop_in_0bsd_replacement_ready": drop_in_release_ready,
            "exact_table_compatible_replacement_ready": exact_ready,
            "exact_compatibility_claim_boundary_documented": claim_boundary_documented,
        },
        "load_errors": load_errors,
        "passing_gate_ids": passing_ids,
        "blocking_gate_ids": blocking_ids,
        "drop_in_blocking_gate_ids": drop_in_blocking_ids,
        "identity_only_blocking_gate_ids": identity_only_blocking_ids,
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
            "m25_compatible_layout_report": (
                rel(M25_COMPATIBLE_LAYOUT_REPORT)
                if M25_COMPATIBLE_LAYOUT_REPORT.exists()
                else "validation/m25_compatible_layout_report.json"
            ),
            "m25_consumer_report": (
                rel(M25_CONSUMER_REPORT)
                if M25_CONSUMER_REPORT.exists()
                else (
                    "research/official_topology/m25/"
                    "m25_consumer_validation.json"
                )
            ),
            "m26_integration_report": (
                rel(M26_INTEGRATION_REPORT)
                if M26_INTEGRATION_REPORT.exists()
                else (
                    "research/official_topology/m26/"
                    "m26_godot_voxel_integration.json"
                )
            ),
            "m26_provenance_report": (
                rel(M26_PROVENANCE_REPORT)
                if M26_PROVENANCE_REPORT.exists()
                else (
                    "research/official_topology/m26/"
                    "m26_provenance_audit.json"
                )
            ),
            "m26_full_build_report": (
                rel(M26_FULL_BUILD_REPORT)
                if M26_FULL_BUILD_REPORT.exists()
                else (
                    "research/official_topology/m26/"
                    "m26_full_godot_voxel_build.json"
                )
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
    print("exact drop-in integration ready:", drop_in_integration_ready)
    print("exact drop-in 0BSD ready:", drop_in_release_ready)
    print("exact claim boundary documented:", claim_boundary_documented)
    print("blocking gates:", len(blocking_ids))
    print("next milestone:", report["next_milestone"]["id"])
    return 0 if analysis_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
