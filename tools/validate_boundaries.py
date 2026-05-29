#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Exhaustive transition-cell boundary validation.

This checks the strongest property this clean-room tetrahedral transition table
can prove without using any third-party Transvoxel table values:

    The mesh boundary produced for every transition case must exactly equal the
    contour produced by applying the same inside/outside signs to the transition
    cell boundary triangles.

This is not a claim of byte compatibility with Eric Lengyel's Transvoxel.cpp.
It is a proof that the generated transition table is internally consistent and
that it does not invent/miss boundary segments for any of the 512 cases.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

EdgeKey = Tuple[int, int]
SegmentKey = Tuple[EdgeKey, EdgeKey]

FACE_RANGES = {
    "high": range(0, 8),
    "low": range(8, 10),
    "y_min": range(10, 13),
    "x_max": range(13, 16),
    "y_max": range(16, 19),
    "x_min": range(19, 22),
}


def edge_key(a: int, b: int) -> EdgeKey:
    if a == b:
        raise ValueError("edge cannot connect a sample to itself")
    return (a, b) if a < b else (b, a)


def segment_key(a: EdgeKey, b: EdgeKey) -> SegmentKey:
    return (a, b) if a <= b else (b, a)


def sign_for_sample(case_index: int, sample_id: int) -> bool:
    if 0 <= sample_id <= 8:
        return (case_index & (1 << sample_id)) != 0
    if sample_id == 9:
        return sign_for_sample(case_index, 0)
    if sample_id == 10:
        return sign_for_sample(case_index, 2)
    if sample_id == 11:
        return sign_for_sample(case_index, 6)
    if sample_id == 12:
        return sign_for_sample(case_index, 8)
    if sample_id == 13:
        return sign_for_sample(case_index, 4)
    raise ValueError(f"unknown sample id {sample_id}")


def contour_for_boundary_triangle(case_index: int, tri: Sequence[int]) -> List[SegmentKey]:
    crossings: List[EdgeKey] = []
    for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
        if sign_for_sample(case_index, a) != sign_for_sample(case_index, b):
            crossings.append(edge_key(a, b))
    if not crossings:
        return []
    if len(crossings) != 2:
        raise AssertionError(f"triangle contour should have 0 or 2 crossings, got {crossings}")
    return [segment_key(crossings[0], crossings[1])]


def expected_segments_by_face(table: Dict[str, object], case_index: int) -> Dict[str, List[SegmentKey]]:
    boundary = [tuple(int(v) for v in tri) for tri in table["boundary_triangles"]]
    out: Dict[str, List[SegmentKey]] = {name: [] for name in FACE_RANGES}
    for face_name, indexes in FACE_RANGES.items():
        for i in indexes:
            out[face_name].extend(contour_for_boundary_triangle(case_index, boundary[i]))
    return out


def expected_all_segments(table: Dict[str, object], case_index: int) -> List[SegmentKey]:
    result: List[SegmentKey] = []
    by_face = expected_segments_by_face(table, case_index)
    for segs in by_face.values():
        result.extend(segs)
    return result


def actual_boundary_segments(case: Dict[str, object]) -> List[SegmentKey]:
    vertex_keys: List[EdgeKey] = []
    for v in case["vertices"]:
        a, b = v["samples"]
        vertex_keys.append(edge_key(int(a), int(b)))

    edge_counts: collections.Counter[Tuple[int, int]] = collections.Counter()
    for tri in case["triangles"]:
        ids = [int(i) for i in tri["vertices"]]
        for a, b in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            if a != b:
                edge_counts[(a, b) if a < b else (b, a)] += 1

    out: List[SegmentKey] = []
    for (a, b), count in edge_counts.items():
        if count == 1:
            out.append(segment_key(vertex_keys[a], vertex_keys[b]))
    return out


def validate(table: Dict[str, object]) -> Dict[str, object]:
    failures = []
    total_expected = 0
    total_actual = 0
    per_face_counts = {name: 0 for name in FACE_RANGES}

    for case in table["cases"]:
        case_index = int(case["case"])
        expected_by_face = expected_segments_by_face(table, case_index)
        expected = collections.Counter(expected_all_segments(table, case_index))
        actual = collections.Counter(actual_boundary_segments(case))
        total_expected += sum(expected.values())
        total_actual += sum(actual.values())
        for name, segs in expected_by_face.items():
            per_face_counts[name] += len(segs)
        if expected != actual:
            failures.append({
                "case": case_index,
                "missing": [repr(k) for k, v in (expected - actual).items() for _ in range(v)],
                "extra": [repr(k) for k, v in (actual - expected).items() for _ in range(v)],
                "expected_count": sum(expected.values()),
                "actual_count": sum(actual.values()),
            })

    return {
        "status": "PASS" if not failures else "FAIL",
        "case_count": len(table["cases"]),
        "total_expected_boundary_segments": total_expected,
        "total_actual_boundary_segments": total_actual,
        "per_face_expected_segments": per_face_counts,
        "failure_count": len(failures),
        "failures": failures[:50],
        "truncated_failures": max(0, len(failures) - 50),
        "meaning": (
            "Every generated transition case exposes exactly the same boundary contour "
            "as the documented transition-cell boundary triangulation. This proves internal "
            "boundary consistency of this clean-room table, not identity with any external table."
        ),
    }


def write_report(result: Dict[str, object], path: Path) -> None:
    lines = [
        "# Boundary Validation Report",
        "",
        f"Status: **{result['status']}**",
        "",
        f"Cases checked: {result['case_count']}",
        f"Expected boundary segments: {result['total_expected_boundary_segments']}",
        f"Actual boundary segments: {result['total_actual_boundary_segments']}",
        f"Failures: {result['failure_count']}",
        "",
        "## Per-face expected segment counts",
        "",
    ]
    for name, count in result["per_face_expected_segments"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Meaning", "", str(result["meaning"]), ""])
    if result["failure_count"]:
        lines.extend(["## First failures", ""])
        for failure in result["failures"]:
            lines.append(f"- case {failure['case']}: missing={len(failure['missing'])}, extra={len(failure['extra'])}")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default="generated/transition_tables.json")
    parser.add_argument("--out", default="validation/boundary_report.json")
    parser.add_argument("--md", default="validation/boundary_report.md")
    args = parser.parse_args()

    table = json.loads(Path(args.table).read_text(encoding="utf-8"))
    result = validate(table)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    write_report(result, Path(args.md))
    print(f"boundary validation: {result['status']} ({result['failure_count']} failures)")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
