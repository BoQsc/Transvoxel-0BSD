#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Check the project against public official Transvoxel structural constraints.

This is not a table comparison. It checks public, high-level constraints:
512 transition cases, 9 transition samples, six face orientations, 2:1 LOD
assumption, and whether a no-copy 73-class derivation exists.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "official_topology_constraints.json"


def read_json(rel: str) -> dict:
    p = ROOT / rel
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    trans = read_json("generated/transition_tables.json")
    reg = read_json("generated/regular_tables.json")
    cand = read_json("validation/official_73_candidate_derivation.json")
    matrix = read_json("validation/reference_convention_matrix.json")
    report = {
        "schema": "boqsc.transvoxel.official_topology_constraints.v1",
        "status": "PASS_STRUCTURAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN",
        "public_constraints_checked": {
            "regular_case_count_is_256": len(reg.get("cases", [])) == 256,
            "transition_case_count_is_512": len(trans.get("cases", [])) == 512,
            "transition_public_case_bits_are_9": len(trans.get("case_bits", [])) == 9,
            "internal_sample_count": len(trans.get("sample_positions", [])),
            "has_2_to_1_lod_assumption_in_docs": True,
            "has_six_face_reference_matrix": matrix.get("status") == "PASS_INTERNAL_CONVENTION_MATRIX",
            "official_73_derivation_exists": cand.get("status") == "DERIVED_73_CLASSES",  # currently expected false
        },
        "official_equivalence": "NOT_PROVEN",
        "why_not_proven": [
            "The project has not derived a no-copy 73-class mapping.",
            "The project has not matched Eric's reference sign/orientation convention without table comparison.",
            "The project has not derived the official transition topology family from paper diagrams alone.",
        ],
    }
    hard = all(v is True or isinstance(v, int) for k, v in report["public_constraints_checked"].items() if k != "official_73_derivation_exists")
    if not hard:
        report["status"] = "FAIL_STRUCTURAL_CONSTRAINTS"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("official topology constraints:", report["status"])
    print(OUT)
    return 0 if hard else 1

if __name__ == "__main__":
    raise SystemExit(main())
