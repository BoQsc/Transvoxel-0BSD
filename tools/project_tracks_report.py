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
            },
            "official_topology_research": {
                "status": "IN_PROGRESS" if official_track_ok else "MISSING_FILES",
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
        },
        "meaning": (
            "The independent core can be released/evaluated independently. "
            "The published transition reference convention, transition "
            "topology behavior, and clean-room regular-cell behavior are "
            "proven by M18-M20. M21 proves the default clean-room M4 "
            "transition export and public C/C++ consumer contract; exact "
            "table compatibility remains separate."
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
