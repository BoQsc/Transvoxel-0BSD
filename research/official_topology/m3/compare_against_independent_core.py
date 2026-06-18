#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compare M3 structural output with the current independent tetrahedral core."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Optional

from m3_core import (
    ambiguity_flags,
    boundary_segments_by_face,
    contract_segments_to_anchor_pairings,
    derive_case_candidate,
    derive_research_classes,
    flatten_segments,
    independent_case_boundary_segments,
    json_segment,
)

ROOT = Path(__file__).resolve().parents[3]
M3_DIR = Path(__file__).resolve().parent
OUT = M3_DIR / "independent_core_comparison.json"


def pairing_counter(report: Dict[str, object]) -> Counter:
    return Counter(tuple(tuple(int(x) for x in edge) for edge in pair)
                   for pair in report["pairings"])


def build_report() -> Dict[str, object]:
    table_path = ROOT / "generated" / "transition_tables.json"
    table = json.loads(table_path.read_text(encoding="utf-8"))
    class_partition = derive_research_classes()
    candidate_path = M3_DIR / "candidate_triangulations.json"
    candidate_counts = {}
    if candidate_path.exists():
        candidate_report = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate_counts = {
            int(case["case"]): int(case.get("triangle_count", 0))
            for case in candidate_report.get("cases", [])
        }

    exact_matches = []
    contracted_matches = []
    contracted_mismatches = []
    mismatch_class_ids = set()
    mismatch_ambiguity_counts: Counter[str] = Counter()
    independent_triangle_total = 0
    candidate_triangle_total = 0
    triangle_count_matches = 0

    for case_record in table["cases"]:
        case_index = int(case_record["case"])
        official_segments = flatten_segments(boundary_segments_by_face(case_index))
        independent_segments = independent_case_boundary_segments(case_record)
        if Counter(official_segments) == Counter(independent_segments):
            exact_matches.append(case_index)

        official_pairings = contract_segments_to_anchor_pairings(official_segments)
        independent_pairings = contract_segments_to_anchor_pairings(independent_segments)
        pairing_match = (
            pairing_counter(official_pairings) == pairing_counter(independent_pairings)
            and official_pairings["unused_segment_count"] == 0
            and independent_pairings["unused_segment_count"] == 0
        )
        if pairing_match:
            contracted_matches.append(case_index)
        else:
            contracted_mismatches.append({
                "case": case_index,
                "research_class_id": class_partition["case_to_research_class"][case_index],
                "ambiguity": ambiguity_flags(case_index),
                "m3_pairings": [
                    json_segment(pair)
                    for pair in official_pairings["pairings"]
                ],
                "independent_pairings": [
                    json_segment(pair)
                    for pair in independent_pairings["pairings"]
                ],
                "m3_unused_segments": official_pairings["unused_segment_count"],
                "independent_unused_segments": independent_pairings["unused_segment_count"],
            })
            mismatch_class_ids.add(
                class_partition["case_to_research_class"][case_index]
            )
            flags = ambiguity_flags(case_index)
            if flags["has_full_resolution_ambiguity"]:
                mismatch_ambiguity_counts["full_resolution"] += 1
            if flags["has_half_resolution_ambiguity"]:
                mismatch_ambiguity_counts["half_resolution"] += 1
            if not flags["has_any_ambiguity"]:
                mismatch_ambiguity_counts["no_ambiguity"] += 1

        independent_count = len(case_record["triangles"])
        candidate_count = candidate_counts.get(case_index)
        if candidate_count is None:
            candidate_count = int(
                derive_case_candidate(case_index).get("triangle_count", 0)
            )
        independent_triangle_total += independent_count
        candidate_triangle_total += candidate_count
        if independent_count == candidate_count:
            triangle_count_matches += 1

    expected_distinct = (
        len(exact_matches) < 512
        and len(contracted_mismatches) > 0
        and mismatch_ambiguity_counts["no_ambiguity"] == 0
    )
    return {
        "schema": "boqsc.transvoxel.official_topology.m3.independent_comparison.v1",
        "status": (
            "PASS_COMPARISON_INDEPENDENT_CORE_IS_STRUCTURALLY_DISTINCT"
            if expected_distinct else "FAIL_OR_UNEXPECTED_COMPARISON_RESULT"
        ),
        "comparison_boundary": (
            "No external table values are used. M3 public-rule contours are "
            "compared only with this repository's independent generated table."
        ),
        "case_count": 512,
        "exact_boundary_segment_match_count": len(exact_matches),
        "exact_boundary_segment_match_cases": exact_matches,
        "contracted_anchor_connectivity_match_count": len(contracted_matches),
        "contracted_anchor_connectivity_mismatch_count": len(contracted_mismatches),
        "contracted_anchor_connectivity_mismatch_research_class_count": len(mismatch_class_ids),
        "mismatch_ambiguity_counts": dict(sorted(mismatch_ambiguity_counts.items())),
        "first_contracted_mismatches": contracted_mismatches[:40],
        "independent_total_triangle_count": independent_triangle_total,
        "m3_candidate_total_triangle_count": candidate_triangle_total,
        "per_case_triangle_count_match_count": triangle_count_matches,
        "interpretation": [
            "The independent tetrahedral core and M3 use different geometric boundary segment families.",
            "After contracting the independent core's extra diagonal/interior boundary vertices, non-ambiguous connectivity agrees.",
            "Remaining connectivity mismatches occur only in ambiguity-bearing cases, which is the expected fault line between the constructions.",
            "This comparison does not establish that M3 triangulations are the official triangulations.",
        ],
        "official_equivalence": "NOT_PROVEN",
    }


def main(output: Optional[Path] = None) -> Dict[str, object]:
    report = build_report()
    target = output or OUT
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("M3 independent-core comparison:", report["status"])
    print(
        "contracted connectivity:",
        report["contracted_anchor_connectivity_match_count"],
        "match /",
        report["contracted_anchor_connectivity_mismatch_count"],
        "mismatch",
    )
    print(target)
    return report


if __name__ == "__main__":
    result = main()
    raise SystemExit(0 if str(result["status"]).startswith("PASS_") else 1)
