#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate transition-cell strips generated from deterministic density fields.

This is a chunk-level seam test, but intentionally still table-only: it does not
need Godot, OpenGL, or Blender. It builds many neighboring transition cells from
sampled SDF-like sign fields and checks that every shared side boundary has the
same normalized contour fingerprint on both cells.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_boundaries import expected_segments_by_face  # noqa: E402
from validate_neighbors import load_positions, segment_fingerprint  # noqa: E402

Field = Callable[[int, int, int], float]


def make_fields() -> Dict[str, Field]:
    def plane_x(x: int, y: int, seed: int) -> float:
        return x - (5 + seed % 3)

    def plane_y(x: int, y: int, seed: int) -> float:
        return y - (4 + seed % 4)

    def diagonal(x: int, y: int, seed: int) -> float:
        return x + y - (8 + seed % 5)

    def circle(x: int, y: int, seed: int) -> float:
        cx = 6 + (seed % 3)
        cy = 6 + ((seed // 2) % 3)
        r = 5 + (seed % 2)
        return (x - cx) * (x - cx) + (y - cy) * (y - cy) - r * r

    def saddle(x: int, y: int, seed: int) -> float:
        return (x - 6) * (x - 6) - (y - 6) * (y - 6) + seed - 2

    def hash_noise(x: int, y: int, seed: int) -> float:
        n = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
        n = (n ^ (n >> 13)) * 1274126177
        n = n ^ (n >> 16)
        return -1.0 if (n & 1) else 1.0

    def wavy(x: int, y: int, seed: int) -> float:
        return math.sin((x + seed) * 0.7) + math.cos((y - seed) * 0.55)

    return {
        "plane_x": plane_x,
        "plane_y": plane_y,
        "diagonal": diagonal,
        "circle": circle,
        "saddle": saddle,
        "hash_noise": hash_noise,
        "wavy": wavy,
    }


def sample_inside(field: Field, gx: int, gy: int, seed: int) -> bool:
    return field(gx, gy, seed) < 0.0


def case_for_cell(field: Field, cx: int, cy: int, seed: int) -> int:
    case_index = 0
    sample_id = 0
    for sy in range(3):
        for sx in range(3):
            gx = cx * 2 + sx
            gy = cy * 2 + sy
            if sample_inside(field, gx, gy, seed):
                case_index |= 1 << sample_id
            sample_id += 1
    return case_index


def face_fp(table: Dict[str, object], positions, case_index: int, face: str):
    case_faces = expected_segments_by_face(table, case_index)
    return segment_fingerprint(face, case_faces[face], positions)


def validate(table: Dict[str, object], size: int, seeds: int) -> Dict[str, object]:
    fields = make_fields()
    positions = load_positions(table)
    failures: List[Dict[str, object]] = []
    strips_checked = 0
    shared_faces_checked = 0

    for field_name, field in fields.items():
        for seed in range(seeds):
            cases = [[case_for_cell(field, x, y, seed) for x in range(size)] for y in range(size)]
            strips_checked += 1

            for y in range(size):
                for x in range(size - 1):
                    left = cases[y][x]
                    right = cases[y][x + 1]
                    a = face_fp(table, positions, left, "x_max")
                    b = face_fp(table, positions, right, "x_min")
                    shared_faces_checked += 1
                    if a != b:
                        failures.append({
                            "field": field_name,
                            "seed": seed,
                            "cell_a": [x, y],
                            "cell_b": [x + 1, y],
                            "face_a": "x_max",
                            "face_b": "x_min",
                            "case_a": left,
                            "case_b": right,
                        })

            for y in range(size - 1):
                for x in range(size):
                    lower = cases[y][x]
                    upper = cases[y + 1][x]
                    a = face_fp(table, positions, lower, "y_max")
                    b = face_fp(table, positions, upper, "y_min")
                    shared_faces_checked += 1
                    if a != b:
                        failures.append({
                            "field": field_name,
                            "seed": seed,
                            "cell_a": [x, y],
                            "cell_b": [x, y + 1],
                            "face_a": "y_max",
                            "face_b": "y_min",
                            "case_a": lower,
                            "case_b": upper,
                        })

    return {
        "status": "PASS" if not failures else "FAIL",
        "grid_size": size,
        "seed_count": seeds,
        "field_count": len(fields),
        "fields": list(fields),
        "strips_checked": strips_checked,
        "shared_faces_checked": shared_faces_checked,
        "failure_count": len(failures),
        "failures": failures[:100],
        "truncated_failures": max(0, len(failures) - 100),
        "meaning": (
            "Many neighboring transition-cell strips were sampled from deterministic sign fields. "
            "Every shared side face had matching contour fingerprints. This catches side cracks "
            "that would appear between transition cells in a real chunk seam strip."
        ),
    }


def write_report(result: Dict[str, object], path: Path) -> None:
    lines = [
        "# Chunk Strip Validation Report",
        "",
        f"Status: **{result['status']}**",
        "",
        f"Grid size: {result['grid_size']} x {result['grid_size']}",
        f"Fields: {result['field_count']} ({', '.join(result['fields'])})",
        f"Seeds per field: {result['seed_count']}",
        f"Strips checked: {result['strips_checked']}",
        f"Shared faces checked: {result['shared_faces_checked']}",
        f"Failures: {result['failure_count']}",
        "",
        "## Meaning",
        "",
        str(result["meaning"]),
        "",
    ]
    if result["failure_count"]:
        lines.extend(["## First failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default="generated/transition_tables.json")
    parser.add_argument("--out", default="validation/chunk_report.json")
    parser.add_argument("--md", default="validation/chunk_report.md")
    parser.add_argument("--size", type=int, default=8)
    parser.add_argument("--seeds", type=int, default=12)
    args = parser.parse_args()

    table = json.loads(Path(args.table).read_text(encoding="utf-8"))
    result = validate(table, args.size, args.seeds)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
    write_report(result, Path(args.md))
    print(f"chunk strip validation: {result['status']} ({result['shared_faces_checked']} shared faces)")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
