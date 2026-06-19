#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"


def read_json(rel: str) -> dict:
    p = ROOT / rel
    if not p.exists():
        return {"status": "MISSING", "path": rel}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "BROKEN_JSON", "path": rel, "error": repr(exc)}


def main() -> int:
    independent_required = [
        "core/independent/include/transvoxel.h",
        "core/independent/src/transvoxel.c",
        "core/independent/generated/transvoxel_tables.h",
        "core/independent/MANIFEST.json",
        "core/independent/README.md",
    ]
    missing_independent = [rel for rel in independent_required if not (ROOT / rel).exists()]
    official_required = [
        "research/official_topology/README.md",
        "research/official_topology/derive_transition_classes.py",
        "research/official_topology/derive_reference_convention.py",
        "research/official_topology/topology_notes.md",
    ]
    missing_official = [rel for rel in official_required if not (ROOT / rel).exists()]

    strict = read_json("validation/strict_correctness_audit.json")
    topology = read_json("validation/topology_signature_report.json")
    official = read_json("validation/official_equivalence_research_report.json")
    class_derivation = read_json("validation/official_transition_class_derivation.json")
    ref = read_json("validation/official_reference_convention_research.json")
    cand73 = read_json("validation/official_73_candidate_derivation.json")
    ref_matrix = read_json("validation/reference_convention_matrix.json")
    constraints = read_json("validation/official_topology_constraints.json")
    published_topology = read_json(
        "validation/published_transition_topology_report.json"
    )
    regular_equivalence = read_json(
        "validation/regular_cell_equivalence_report.json"
    )
    consumer_compatibility = read_json(
        "validation/consumer_compatibility_report.json"
    )
    readiness = read_json("validation/m4_replacement_readiness_report.json")
    claim_boundary = read_json(
        "validation/exact_compatibility_claim_boundary_report.json"
    )
    official_oracle = read_json(
        "validation/official_oracle_comparison_report.json"
    )
    m24_exact_topology = read_json(
        "validation/m24_exact_topology_report.json"
    )
    m25_compatible_layout = read_json(
        "validation/m25_compatible_layout_report.json"
    )
    m25_consumer = read_json(
        "research/official_topology/m25/m25_consumer_validation.json"
    )
    m26_integration = read_json(
        "research/official_topology/m26/m26_godot_voxel_integration.json"
    )
    m26_provenance = read_json(
        "research/official_topology/m26/m26_provenance_audit.json"
    )
    m26_full_build = read_json(
        "research/official_topology/m26/m26_full_godot_voxel_build.json"
    )
    m27_terminal = read_json(
        "research/official_topology/m27/m27_terminal_audit.json"
    )
    terminal_m27 = (
        m27_terminal.get("status")
        == "TERMINAL_M27_EXACT_0BSD_REPLACEMENT_NOT_ACHIEVED"
        and m27_terminal.get("decision", {}).get("terminal") is True
    )

    independent_ok = not missing_independent
    official_track_ok = not missing_official
    report = {
        "schema": "boqsc.transvoxel.project_tracks_report.v1",
        "status": "PASS" if independent_ok and official_track_ok else "FAIL",
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "UNKNOWN",
        "tracks": {
            "independent_core": {
                "status": "PASS" if independent_ok else "MISSING_FILES",
                "purpose": "Proven practical 0BSD drop-in core.",
                "missing": missing_independent,
                "official_equivalence": "NOT_CLAIMED",
                "functional_transvoxel_cpp_replacement": (
                    "PROVEN"
                    if readiness.get("decisions", {}).get(
                        "functional_full_replacement_ready"
                    )
                    is True
                    else "NOT_PROVEN"
                ),
                "consumer_compatibility": consumer_compatibility.get(
                    "functional_transvoxel_cpp_consumer_compatibility",
                    "NOT_PROVEN",
                ),
                "exact_compatibility_claim_boundary": claim_boundary.get(
                    "status",
                    "NOT_PROVEN",
                ),
            },
            "official_topology_research": {
                "status": (
                    "TERMINAL_NOT_ACHIEVED"
                    if official_track_ok and terminal_m27
                    else "IN_PROGRESS"
                    if official_track_ok
                    else "MISSING_FILES"
                ),
                "purpose": "Research official 73-class/topology/reference-convention equivalence without copying MIT table values.",
                "missing": missing_official,
                "official_73_class_mapping": "NOT_PROVEN",
                "reference_convention_equivalence": ref_matrix.get(
                    "official_reference_equivalence",
                    "NOT_PROVEN",
                ),
                "original_topology_equivalence": "NOT_PROVEN",
                "published_transition_topology_behavior": (
                    published_topology.get(
                        "published_transition_topology_behavior",
                        "NOT_PROVEN",
                    )
                ),
                "clean_room_regular_cell_equivalence": (
                    regular_equivalence.get(
                        "functional_regular_cell_equivalence",
                        "NOT_PROVEN",
                    )
                ),
                "official_oracle_baseline": official_oracle.get(
                    "status",
                    "NOT_RUN",
                ),
                "exact_replacement_ready": official_oracle.get(
                    "decisions",
                    {},
                ).get("exact_replacement_ready", False),
                "exact_oriented_topology_identity": (
                    "PROVEN"
                    if m24_exact_topology.get("decisions", {}).get(
                        "exact_topology_identity"
                    )
                    is True
                    else "NOT_PROVEN"
                ),
                "exact_0bsd_provenance_cleared": (
                    m27_terminal.get("decision", {}).get(
                        "exact_candidate_0bsd_provenance_cleared",
                        m24_exact_topology.get("decisions", {}).get(
                            "exact_0bsd_provenance_cleared",
                            False,
                        ),
                    )
                ),
                "exact_0bsd_goal_achieved": m27_terminal.get(
                    "decision", {}
                ).get("exact_0bsd_goal_achieved", False),
                "terminal_roadmap_decision": m27_terminal.get(
                    "status", "NOT_RUN"
                ),
                "compatible_transvoxel_cpp_data_layout": (
                    m25_compatible_layout.get("decisions", {}).get(
                        "compatible_struct_and_symbol_surface",
                        False,
                    )
                ),
                "unchanged_style_cpp_consumer": m25_consumer.get(
                    "status",
                    "NOT_RUN",
                ),
                "godot_voxel_table_integration": m26_integration.get(
                    "status",
                    "NOT_RUN",
                ),
                "godot_voxel_full_gdextension_build": m26_full_build.get(
                    "status",
                    "NOT_RUN",
                ),
                "exact_drop_in_integration_ready": readiness.get(
                    "decisions",
                    {},
                ).get("exact_drop_in_integration_ready", False),
                "exact_drop_in_0bsd_replacement_ready": readiness.get(
                    "decisions",
                    {},
                ).get("exact_drop_in_0bsd_replacement_ready", False),
                "exact_candidate_provenance_audit": m26_provenance.get(
                    "status",
                    "NOT_RUN",
                ),
            },
        },
        "supporting_reports": {
            "strict_correctness_audit_status": strict.get("status"),
            "transvoxel_style_proof": strict.get("transvoxel_style_proof"),
            "official_transvoxel_equivalence_proof": strict.get("official_transvoxel_equivalence_proof"),
            "topology_signature_status": topology.get("status"),
            "official_equivalence_research_status": official.get("status"),
            "official_transition_class_derivation_status": class_derivation.get("status"),
            "official_reference_convention_status": ref.get("status"),
            "official_73_candidate_derivation_status": cand73.get("status"),
            "reference_convention_matrix_status": ref_matrix.get("status"),
            "official_topology_constraints_status": constraints.get("status"),
            "published_transition_topology_status": published_topology.get(
                "status"
            ),
            "regular_cell_equivalence_status": regular_equivalence.get(
                "status"
            ),
            "consumer_compatibility_status": consumer_compatibility.get(
                "status"
            ),
            "replacement_readiness_status": readiness.get("status"),
            "exact_compatibility_claim_boundary_status": claim_boundary.get(
                "status"
            ),
            "official_oracle_comparison_status": official_oracle.get(
                "status"
            ),
            "m24_exact_topology_status": m24_exact_topology.get("status"),
            "m25_compatible_layout_status": m25_compatible_layout.get(
                "status"
            ),
            "m25_consumer_status": m25_consumer.get("status"),
            "m26_godot_voxel_integration_status": m26_integration.get(
                "status"
            ),
            "m26_provenance_audit_status": m26_provenance.get("status"),
            "m26_full_godot_voxel_build_status": m26_full_build.get(
                "status"
            ),
            "m27_terminal_audit_status": m27_terminal.get("status"),
        },
        "meaning": (
            "The independent core can be released/evaluated independently. "
            "The published transition reference convention, transition "
            "topology behavior, and clean-room regular-cell behavior are "
            "proven by M18-M20. M21 proves the default clean-room M4 "
            "transition export and public C/C++ consumer contract. M22 locks "
            "the exact compatibility claim boundary. M23 measures every "
            "regular and transition case against the verified external "
            "official oracle. M24 proves exact edge-labeled oriented topology; "
            "M25 adds compatible packed reuse semantics, original data symbols "
            "and array capacities, and an unchanged-style C++ consumer. M26 "
            "proves the pinned Godot Voxel table integration with zero "
            "mismatches and a complete Zig-built Windows GDExtension DLL. "
            "M27 is terminal: published rules allow multiple legal interiors, "
            "the independent deterministic topology is not exact, and the "
            "exact candidate depends on MIT-oracle-calibrated selections. The "
            "exact 0BSD goal is not achieved; there is no automatic M28."
        ),
    }
    VALIDATION.mkdir(exist_ok=True)
    (VALIDATION / "project_tracks_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("project tracks:", report["status"])
    print("independent_core:", report["tracks"]["independent_core"]["status"])
    print("official_topology_research:", report["tracks"]["official_topology_research"]["status"])
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
