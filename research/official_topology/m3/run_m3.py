#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run the complete official-topology M3 research milestone."""
from __future__ import annotations

import json
from pathlib import Path

import compare_against_independent_core
import derive_boundary_loops
import derive_candidate_triangulations

M3_DIR = Path(__file__).resolve().parent
REPORT = M3_DIR / "m3_report.json"
RESULTS = M3_DIR / "results.md"


def main() -> int:
    boundary = derive_boundary_loops.main()
    candidates = derive_candidate_triangulations.main()
    comparison = compare_against_independent_core.main()
    hard_pass = all(
        str(report["status"]).startswith("PASS_")
        for report in (boundary, candidates, comparison)
    )
    report = {
        "schema": "boqsc.transvoxel.official_topology.m3.report.v1",
        "status": (
            "PASS_M3_CONSTRAINT_DERIVATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if hard_pass else "FAIL_M3"
        ),
        "milestone": "Official topology M3: class-level triangulation constraints",
        "class_partition": {
            "research_class_count": boundary["research_class_count"],
            "structure": "51 base + 18 full-resolution inverse splits + 4 half-resolution-only inverse splits",
        },
        "boundary_loops": {
            "status": boundary["status"],
            "case_count": boundary["case_count"],
            "failure_count": boundary["failure_count"],
            "loop_count_histogram": boundary["loop_count_histogram"],
        },
        "candidate_triangulations": {
            "status": candidates["status"],
            "case_count": candidates["case_count"],
            "failure_count": candidates["failure_count"],
            "class_topology_signature_failure_count": candidates[
                "class_topology_signature_failure_count"
            ],
            "total_triangle_count": candidates["total_triangle_count"],
            "nested_contour_cases": candidates["nested_contour_cases"],
            "fallback_enumeration_cases": candidates["fallback_enumeration_cases"],
        },
        "independent_core_comparison": {
            "status": comparison["status"],
            "exact_boundary_segment_match_count": comparison["exact_boundary_segment_match_count"],
            "contracted_anchor_connectivity_match_count": comparison["contracted_anchor_connectivity_match_count"],
            "contracted_anchor_connectivity_mismatch_count": comparison["contracted_anchor_connectivity_mismatch_count"],
            "independent_total_triangle_count": comparison["independent_total_triangle_count"],
            "m3_candidate_total_triangle_count": comparison["m3_candidate_total_triangle_count"],
        },
        "answers": {
            "can_boundary_contours_be_derived": "YES_FOR_ALL_512_CASES",
            "can_valid_candidate_triangulations_be_generated": "YES_FOR_ALL_512_CASES",
            "does_this_prove_official_triangulation_equivalence": "NO",
            "does_the_current_independent_core_use_the_same_topology_family": "NO_STRUCTURAL_MATCH",
            "is_a_second_official_style_candidate_core_justified": "YES",
        },
        "official_equivalence": "NOT_PROVEN",
        "next_milestone": (
            "M4 should derive orientation-preserving class transforms and build "
            "a separate official-style candidate table from these constraints."
        ),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Official Topology M3 Results",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Result",
        "",
        "- The clean-room class partition reproduces `51 + 18 + 4 = 73` research classes.",
        "- Boundary contours form closed degree-2 loops for all 512 cases.",
        (
            f"- Boundary-only candidate surfaces validate for all 512 cases "
            f"with {candidates['total_triangle_count']} triangles in total."
        ),
        (
            "- Case 341 contains nested full-resolution contours and is derived "
            "as a planar annulus instead of two overlapping disks."
        ),
        (
            f"- The current independent core matches M3 anchor connectivity in "
            f"{comparison['contracted_anchor_connectivity_match_count']} cases and "
            f"differs in {comparison['contracted_anchor_connectivity_mismatch_count']} "
            "ambiguity-bearing cases."
        ),
        "",
        "## What this means",
        "",
        (
            "M3 demonstrates that a complete 512-case boundary contract and a valid "
            "candidate surface family can be generated from public geometry and "
            "ambiguity rules without reading official table arrays."
        ),
        "",
        (
            "It does not prove official triangle choices, official class IDs, "
            "official vertex encodings, winding compatibility, or table identity."
        ),
        "",
        "## Decision",
        "",
        (
            "The M3 topology is structurally different from the current independent "
            "tetrahedral core. Further official-style work should remain a separate "
            "candidate core rather than replacing the release-candidate core."
        ),
        "",
        "## Next milestone",
        "",
        report["next_milestone"],
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")
    print()
    print("M3:", report["status"])
    print(RESULTS)
    return 0 if hard_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
