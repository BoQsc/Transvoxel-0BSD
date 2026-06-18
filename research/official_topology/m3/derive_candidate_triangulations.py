#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Generate and validate clean-room candidate transition triangulations."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Optional

from m3_core import (
    derive_case_candidate,
    derive_research_classes,
    histogram,
    serialize_case_candidate,
)

M3_DIR = Path(__file__).resolve().parent
OUT = M3_DIR / "candidate_triangulations.json"


def build_report() -> Dict[str, object]:
    class_partition = derive_research_classes()
    cases = []
    failures = []
    total_triangles = 0
    triangle_counts = []
    method_counts: Counter[str] = Counter()
    nesting_cases = []
    fallback_cases = []

    raw_cases = []
    for case_index in range(512):
        record = derive_case_candidate(case_index)
        raw_cases.append(record)
        if record["status"] != "PASS":
            failures.append({
                "case": case_index,
                "status": record["status"],
                "validation": record.get("validation"),
            })
        triangle_count = int(record.get("triangle_count", 0))
        total_triangles += triangle_count
        triangle_counts.append(triangle_count)
        for method in record.get("methods", []):
            method_counts[str(method)] += 1
        if record.get("nesting"):
            nesting_cases.append(case_index)
        if "enumerated_nonintersecting_loop_triangulations" in record.get("methods", []):
            fallback_cases.append(case_index)
        serialized = serialize_case_candidate(record)
        serialized["research_class_id"] = class_partition["case_to_research_class"][case_index]
        cases.append(serialized)

    class_summaries = []
    class_signature_failures = []
    for class_record in class_partition["classes"]:
        representative = int(class_record["representative_case"])
        candidate = raw_cases[representative]
        member_signatures = {
            (
                tuple(raw_cases[int(case_index)].get("loop_lengths", [])),
                int(raw_cases[int(case_index)].get("triangle_count", 0)),
                len(raw_cases[int(case_index)].get("nesting", [])),
            )
            for case_index in class_record["cases"]
        }
        if len(member_signatures) != 1:
            class_signature_failures.append({
                "research_class_id": class_record["research_class_id"],
                "representative_case": representative,
                "member_signatures": [
                    {
                        "loop_lengths": list(signature[0]),
                        "triangle_count": signature[1],
                        "nested_pair_count": signature[2],
                    }
                    for signature in sorted(member_signatures)
                ],
            })
        class_summaries.append({
            "research_class_id": class_record["research_class_id"],
            "kind": class_record["kind"],
            "representative_case": representative,
            "class_size": class_record["class_size"],
            "loop_lengths": candidate.get("loop_lengths", []),
            "triangle_count": candidate.get("triangle_count", 0),
            "methods": candidate.get("methods", []),
            "candidate_status": candidate.get("status"),
        })

    hard_pass = (
        class_partition["status"].startswith("PASS_")
        and not failures
        and not class_signature_failures
        and len(cases) == 512
    )
    return {
        "schema": "boqsc.transvoxel.official_topology.m3.candidates.v1",
        "status": (
            "PASS_CANDIDATE_TRIANGULATIONS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if hard_pass else "FAIL_CANDIDATE_TRIANGULATIONS"
        ),
        "candidate_model": (
            "Boundary-only minimal disk fillings, except nested planar contours "
            "are filled as annuli. No synthetic center vertex is used."
        ),
        "case_count": len(cases),
        "research_class_count": class_partition["research_class_count"],
        "total_triangle_count": total_triangles,
        "triangle_count_histogram": histogram(triangle_counts),
        "method_case_counts": dict(sorted(method_counts.items())),
        "nested_contour_cases": nesting_cases,
        "fallback_enumeration_cases": fallback_cases,
        "failure_count": len(failures),
        "failures": failures,
        "class_topology_signature_failure_count": len(class_signature_failures),
        "class_topology_signature_failures": class_signature_failures,
        "class_representatives": class_summaries,
        "cases": cases,
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "official_vertex_encoding_equivalence": "NOT_PROVEN",
    }


def main(output: Optional[Path] = None) -> Dict[str, object]:
    report = build_report()
    target = output or OUT
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("M3 candidate triangulations:", report["status"])
    print("triangles:", report["total_triangle_count"])
    print(target)
    return report


if __name__ == "__main__":
    result = main()
    raise SystemExit(0 if str(result["status"]).startswith("PASS_") else 1)
