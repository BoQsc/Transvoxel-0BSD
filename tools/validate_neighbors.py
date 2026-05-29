#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate transition-cell side-face consistency.

This proves that lateral transition-cell faces have deterministic contour
fingerprints. If two neighboring transition cells agree on the shared face
sample signs, they expose the same shared-face contour, so the side seam cannot
crack under this table contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_boundaries import expected_segments_by_face, sign_for_sample  # noqa: E402

Coord = Tuple[Fraction, Fraction, Fraction]
Point2 = Tuple[Fraction, Fraction]
Segment2 = Tuple[Point2, Point2]
Fingerprint = Tuple[Segment2, ...]

SIDE_SAMPLES = {
    "y_min": [0, 1, 2, 9, 10],
    "y_max": [6, 7, 8, 11, 12],
    "x_min": [0, 3, 6, 9, 11],
    "x_max": [2, 5, 8, 10, 12],
}

OPPOSITE = [("y_min", "y_max"), ("x_min", "x_max")]


def load_positions(table: Dict[str, object]) -> Dict[int, Coord]:
    out: Dict[int, Coord] = {}
    for item in table["sample_positions"]:
        x, y, z = item["position"]
        out[int(item["id"])] = (Fraction(str(x)), Fraction(str(y)), Fraction(str(z)))
    return out


def edge_midpoint(edge: Tuple[int, int], pos: Dict[int, Coord]) -> Coord:
    a, b = edge
    pa, pb = pos[a], pos[b]
    return tuple((pa[i] + pb[i]) / 2 for i in range(3))  # type: ignore[return-value]


def project(face: str, p: Coord) -> Point2:
    x, y, z = p
    if face in ("y_min", "y_max"):
        return (x, z)
    if face in ("x_min", "x_max"):
        return (y, z)
    raise ValueError(f"not a side face: {face}")


def segment_fingerprint(face: str, segments, pos: Dict[int, Coord]) -> Fingerprint:
    out: List[Segment2] = []
    for a_edge, b_edge in segments:
        a = project(face, edge_midpoint(a_edge, pos))
        b = project(face, edge_midpoint(b_edge, pos))
        out.append((a, b) if a <= b else (b, a))
    out.sort()
    return tuple(out)


def pattern_for_face(case_index: int, face: str) -> Tuple[int, ...]:
    return tuple(1 if sign_for_sample(case_index, sid) else 0 for sid in SIDE_SAMPLES[face])


def frac_to_text(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def fingerprint_to_json(fp: Fingerprint):
    return [
        [[frac_to_text(p[0]), frac_to_text(p[1])], [frac_to_text(q[0]), frac_to_text(q[1])]]
        for p, q in fp
    ]


def validate(table: Dict[str, object]) -> Dict[str, object]:
    pos = load_positions(table)
    by_face_pattern: Dict[str, Dict[Tuple[int, ...], Fingerprint]] = {face: {} for face in SIDE_SAMPLES}
    disagreements = []

    for case in table["cases"]:
        case_index = int(case["case"])
        expected_faces = expected_segments_by_face(table, case_index)
        for face in SIDE_SAMPLES:
            pattern = pattern_for_face(case_index, face)
            fp = segment_fingerprint(face, expected_faces[face], pos)
            old = by_face_pattern[face].get(pattern)
            if old is None:
                by_face_pattern[face][pattern] = fp
            elif old != fp:
                disagreements.append({
                    "case": case_index,
                    "face": face,
                    "pattern": pattern,
                    "first": fingerprint_to_json(old),
                    "current": fingerprint_to_json(fp),
                })

    opposite_failures = []
    for a, b in OPPOSITE:
        keys = sorted(set(by_face_pattern[a]) | set(by_face_pattern[b]))
        for pattern in keys:
            fa = by_face_pattern[a].get(pattern)
            fb = by_face_pattern[b].get(pattern)
            if fa != fb:
                opposite_failures.append({
                    "faces": [a, b],
                    "pattern": pattern,
                    "first": fingerprint_to_json(fa or tuple()),
                    "second": fingerprint_to_json(fb or tuple()),
                })

    return {
        "status": "PASS" if not disagreements and not opposite_failures else "FAIL",
        "faces_checked": list(SIDE_SAMPLES),
        "patterns_per_face": {k: len(v) for k, v in by_face_pattern.items()},
        "determinism_failures": len(disagreements),
        "opposite_face_failures": len(opposite_failures),
        "first_determinism_failures": disagreements[:20],
        "first_opposite_face_failures": opposite_failures[:20],
        "meaning": (
            "Side-face contours are a pure function of the shared face signs, and opposite "
            "side faces use the same normalized fingerprints. Adjacent transition cells that "
            "share signs therefore expose matching side boundaries."
        ),
    }


def write_report(result: Dict[str, object], path: Path) -> None:
    lines = [
        "# Neighbor Validation Report",
        "",
        f"Status: **{result['status']}**",
        "",
        "## Patterns per side face",
        "",
    ]
    for face, count in result["patterns_per_face"].items():
        lines.append(f"- `{face}`: {count}")
    lines.extend([
        "",
        f"Determinism failures: {result['determinism_failures']}",
        f"Opposite-face failures: {result['opposite_face_failures']}",
        "",
        "## Meaning",
        "",
        str(result["meaning"]),
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default="generated/transition_tables.json")
    parser.add_argument("--out", default="validation/neighbor_report.json")
    parser.add_argument("--md", default="validation/neighbor_report.md")
    args = parser.parse_args()
    table = json.loads(Path(args.table).read_text(encoding="utf-8"))
    result = validate(table)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
    write_report(result, Path(args.md))
    print(f"neighbor validation: {result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
