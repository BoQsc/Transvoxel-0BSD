#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Derive official-style transition-cell boundary contours and loops."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from m3_core import (
    ambiguity_flags,
    boundary_segments_by_face,
    derive_research_classes,
    flatten_segments,
    histogram,
    json_edge,
    json_segment,
    trace_boundary_loops,
)

M3_DIR = Path(__file__).resolve().parent
OUT = M3_DIR / "boundary_loops.json"
CLASS_OUT = M3_DIR / "class_partition.json"


def build_report() -> Dict[str, object]:
    class_partition = derive_research_classes()
    cases = []
    failures = []
    loop_counts = []
    loop_lengths = []
    total_segments = 0
    for case_index in range(512):
        by_face = boundary_segments_by_face(case_index)
        segments = flatten_segments(by_face)
        loop_report = trace_boundary_loops(segments)
        if loop_report["status"] != "PASS":
            failures.append({
                "case": case_index,
                "status": loop_report["status"],
                "bad_degrees": loop_report.get("bad_degrees", {}),
            })
        loops = loop_report.get("loops", [])
        loop_counts.append(len(loops))
        loop_lengths.extend(len(loop) for loop in loops)
        total_segments += len(segments)
        cases.append({
            "case": case_index,
            "research_class_id": class_partition["case_to_research_class"][case_index],
            "inside_count": case_index.bit_count(),
            "ambiguity": ambiguity_flags(case_index),
            "segments_by_face": {
                name: [json_segment(segment) for segment in face_segments]
                for name, face_segments in by_face.items()
            },
            "segment_count": len(segments),
            "loops": [
                [json_edge(vertex) for vertex in loop]
                for loop in loops
            ],
            "loop_lengths": sorted(len(loop) for loop in loops),
        })

    hard_pass = (
        class_partition["status"].startswith("PASS_")
        and not failures
        and len(cases) == 512
    )
    return {
        "schema": "boqsc.transvoxel.official_topology.m3.boundary_loops.v1",
        "status": (
            "PASS_BOUNDARY_LOOPS_DERIVED_OFFICIAL_TRIANGULATION_NOT_PROVEN"
            if hard_pass else "FAIL_BOUNDARY_LOOP_DERIVATION"
        ),
        "no_copy_rule": (
            "Uses public geometry and contour rules only. No official MIT table "
            "arrays, class lookup values, vertex encodings, or triangle arrays are read."
        ),
        "case_count": len(cases),
        "research_class_count": class_partition["research_class_count"],
        "total_boundary_segments": total_segments,
        "loop_count_histogram": histogram(loop_counts),
        "loop_length_histogram": histogram(loop_lengths),
        "failure_count": len(failures),
        "failures": failures,
        "cases": cases,
        "official_equivalence": "NOT_PROVEN",
    }


def main(output: Optional[Path] = None) -> Dict[str, object]:
    report = build_report()
    target = output or OUT
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    class_partition = derive_research_classes()
    CLASS_OUT.write_text(
        json.dumps(class_partition, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print("M3 boundary loops:", report["status"])
    print("research classes:", report["research_class_count"])
    print(target)
    return report


if __name__ == "__main__":
    result = main()
    raise SystemExit(0 if str(result["status"]).startswith("PASS_") else 1)
