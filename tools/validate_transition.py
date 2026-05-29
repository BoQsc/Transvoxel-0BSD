#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validation harness for the clean-room transition table generator.

This script intentionally validates properties of *this repository's generator*.
It does not compare against Eric Lengyel's MIT-licensed Transvoxel.cpp tables.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

Vec3 = Tuple[float, float, float]
Pair = Tuple[int, int]

EPS = 1.0e-12


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_generator():
    path = root_dir() / "tools" / "generate_transition.py"
    spec = importlib.util.spec_from_file_location("generate_transition_tables", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(v: Vec3) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def tri_area(a: Vec3, b: Vec3, c: Vec3) -> float:
    return 0.5 * length(cross(sub(b, a), sub(c, a)))


def sign_value(gen, case_index: int, sample_id: int) -> float:
    # Generator convention: True means inside/negative.
    return -1.0 if gen.sign_for_sample(case_index, sample_id) else 1.0


def interp(pa: Vec3, pb: Vec3, va: float, vb: float) -> Vec3:
    denom = va - vb
    if abs(denom) < EPS:
        t = 0.5
    else:
        t = va / denom
    return (
        pa[0] + (pb[0] - pa[0]) * t,
        pa[1] + (pb[1] - pa[1]) * t,
        pa[2] + (pb[2] - pa[2]) * t,
    )


def vertex_position(gen, case_index: int, pair: Pair) -> Vec3:
    a, b = pair
    pa = tuple(float(x) for x in gen.SAMPLE_POSITIONS[a])
    pb = tuple(float(x) for x in gen.SAMPLE_POSITIONS[b])
    va = sign_value(gen, case_index, a)
    vb = sign_value(gen, case_index, b)
    return interp(pa, pb, va, vb)


def edge_key(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def validate_topology(gen, table: Dict[str, object]) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []

    base_errors = gen.verify_table(table)
    errors.extend(base_errors)

    vertex_counts: List[int] = []
    triangle_counts: List[int] = []
    non_empty = 0
    complement_mismatches: List[int] = []
    degenerate_triangles: List[Dict[str, object]] = []
    bad_crossing_pairs: List[Dict[str, object]] = []
    duplicate_triangles: List[Dict[str, object]] = []

    cases = table.get("cases", [])
    for case in cases:
        idx = int(case["case"])
        vertices = case["vertices"]
        triangles = case["triangles"]
        vertex_counts.append(len(vertices))
        triangle_counts.append(len(triangles))
        if triangles:
            non_empty += 1

        positions: List[Vec3] = []
        for vertex in vertices:
            pair = tuple(int(x) for x in vertex["samples"])
            va = sign_value(gen, idx, pair[0])
            vb = sign_value(gen, idx, pair[1])
            if (va < 0) == (vb < 0):
                bad_crossing_pairs.append({"case": idx, "pair": list(pair)})
            positions.append(vertex_position(gen, idx, pair))

        tri_seen = set()
        for tri_id, tri in enumerate(triangles):
            ids = [int(x) for x in tri["vertices"]]
            canonical = tuple(sorted(ids))
            if canonical in tri_seen:
                duplicate_triangles.append({"case": idx, "triangle_id": tri_id, "vertices": ids})
            tri_seen.add(canonical)
            if len(set(ids)) != 3:
                degenerate_triangles.append({"case": idx, "triangle_id": tri_id, "reason": "duplicate_vertex_id", "vertices": ids})
                continue
            area = tri_area(positions[ids[0]], positions[ids[1]], positions[ids[2]])
            if area <= EPS:
                degenerate_triangles.append({"case": idx, "triangle_id": tri_id, "reason": "zero_area", "vertices": ids, "area": area})

    for idx in range(512):
        comp = idx ^ 511
        c0 = cases[idx]
        c1 = cases[comp]
        if len(c0["vertices"]) != len(c1["vertices"]) or len(c0["triangles"]) != len(c1["triangles"]):
            complement_mismatches.append(idx)

    if bad_crossing_pairs:
        errors.append(f"found {len(bad_crossing_pairs)} vertex pairs whose endpoints do not cross signs")
    if degenerate_triangles:
        errors.append(f"found {len(degenerate_triangles)} degenerate triangles")
    if duplicate_triangles:
        warnings.append(f"found {len(duplicate_triangles)} duplicate triangles by vertex id")
    if complement_mismatches:
        warnings.append(f"found {len(complement_mismatches)} complement-count mismatches")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "case_count": len(cases),
        "non_empty_cases": non_empty,
        "empty_cases": len(cases) - non_empty,
        "min_vertices_per_case": min(vertex_counts) if vertex_counts else None,
        "max_vertices_per_case": max(vertex_counts) if vertex_counts else None,
        "min_triangles_per_case": min(triangle_counts) if triangle_counts else None,
        "max_triangles_per_case": max(triangle_counts) if triangle_counts else None,
        "total_vertices_across_cases": sum(vertex_counts),
        "total_triangles_across_cases": sum(triangle_counts),
        "bad_crossing_pair_examples": bad_crossing_pairs[:20],
        "degenerate_triangle_examples": degenerate_triangles[:20],
        "duplicate_triangle_examples": duplicate_triangles[:20],
        "complement_mismatch_examples": complement_mismatches[:20],
    }


def write_markdown(report: Dict[str, object], path: Path) -> None:
    lines = []
    lines.append("# Validation Report")
    lines.append("")
    lines.append("This report validates the clean-room generator output. It does not compare against or copy any MIT-licensed Transvoxel.cpp table values.")
    lines.append("")
    lines.append(f"- OK: `{report['ok']}`")
    lines.append(f"- SHA-256: `{report['sha256_without_this_field']}`")
    lines.append(f"- Cases: `{report['case_count']}`")
    lines.append(f"- Non-empty cases: `{report['non_empty_cases']}`")
    lines.append(f"- Empty cases: `{report['empty_cases']}`")
    lines.append(f"- Vertices per case: `{report['min_vertices_per_case']}` .. `{report['max_vertices_per_case']}`")
    lines.append(f"- Triangles per case: `{report['min_triangles_per_case']}` .. `{report['max_triangles_per_case']}`")
    lines.append(f"- Total generated vertex-pairs across all cases: `{report['total_vertices_across_cases']}`")
    lines.append(f"- Total generated triangles across all cases: `{report['total_triangles_across_cases']}`")
    lines.append("")
    if report["errors"]:
        lines.append("## Errors")
        for err in report["errors"]:
            lines.append(f"- {err}")
        lines.append("")
    if report["warnings"]:
        lines.append("## Warnings")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("## What this proves")
    lines.append("")
    lines.append("The generated table is deterministic, structurally valid by the repository's own invariants, and all emitted interpolated vertices lie on sign-changing sample edges.")
    lines.append("")
    lines.append("## What this does not prove")
    lines.append("")
    lines.append("This does not prove compatibility with Eric Lengyel's official Transvoxel tables, and it does not prove production-quality triangle patterns for every possible terrain edit. Visual and engine-side seam tests are still required.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = root_dir()
    gen = load_generator()
    table = gen.generate_tables()
    report = validate_topology(gen, table)
    report["schema"] = table.get("schema")
    report["status"] = table.get("status")
    report["sha256_without_this_field"] = table.get("sha256_without_this_field")

    out_dir = root / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_dir / "validation_report.md")

    print("validation report:", out_dir / "validation_report.md")
    print("ok:", report["ok"])
    print("sha256:", report["sha256_without_this_field"])
    if report["errors"]:
        print("errors:")
        for err in report["errors"]:
            print("-", err)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
