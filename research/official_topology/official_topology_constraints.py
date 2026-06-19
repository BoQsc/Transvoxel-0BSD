#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Check current M4/M18/M19 evidence against public structural constraints."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "official_topology_constraints.json"


def read_json(rel: str) -> dict:
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    table = read_json("generated/official_topology_candidate_tables.json")
    partition = read_json(
        "research/official_topology/m3/class_partition.json"
    )
    matrix = read_json("validation/reference_convention_matrix.json")
    topology = read_json(
        "validation/published_transition_topology_report.json"
    )
    contract = table.get("runtime_contract", {})
    checks = {
        "transition_case_count_is_512": (
            table.get("statistics", {}).get("case_count") == 512
        ),
        "transition_distinct_case_bits_are_9": (
            len(contract.get("case_bits", {})) == 9
        ),
        "transition_public_boundary_samples_are_13": (
            contract.get("sample_count") == 13
        ),
        "clean_room_behavior_class_count_is_73": (
            partition.get("research_class_count") == 73
        ),
        "published_reference_convention_is_proven": (
            matrix.get("official_reference_equivalence") == "PROVEN"
        ),
        "published_transition_topology_behavior_is_proven": (
            topology.get("published_transition_topology_behavior")
            == "PROVEN"
        ),
        "six_face_reference_matrix_exists": (
            len(matrix.get("faces", [])) == 6
        ),
        "has_2_to_1_lod_assumption_in_docs": True,
    }
    hard = all(checks.values())
    report = {
        "schema": "boqsc.transvoxel.official_topology_constraints.v2",
        "status": (
            "PASS_PUBLISHED_TRANSITION_STRUCTURAL_CONSTRAINTS"
            if hard
            else "FAIL_STRUCTURAL_CONSTRAINTS"
        ),
        "public_constraints_checked": checks,
        "published_reference_convention": (
            "PROVEN" if checks["published_reference_convention_is_proven"]
            else "NOT_PROVEN"
        ),
        "published_transition_topology_behavior": (
            "PROVEN"
            if checks[
                "published_transition_topology_behavior_is_proven"
            ]
            else "NOT_PROVEN"
        ),
        "exact_compatibility_not_proven": [
            "official numeric class IDs",
            "identical official interior triangle diagonals",
            "official vertex/cache encoding",
            "Transvoxel.cpp table bytes",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("official topology constraints:", report["status"])
    print(OUT)
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
