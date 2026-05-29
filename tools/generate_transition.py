#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
#
# Clean-room transition-cell table generator.
#
# Important:
# This program does not copy Eric Lengyel's MIT-licensed Transvoxel.cpp tables.
# It emits an independent, experimental transition-cell table by applying
# marching tetrahedra to a documented tetrahedralization of a transition cell.
#
# The generated table is NOT claimed to be bit-identical to the official
# Transvoxel lookup table and should be validated visually/geometrically before
# production use.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

SCHEMA = "boqsc.transition_tables.v1"
LICENSE = "0BSD"
STATUS = "experimental_not_drop_in_transvoxel_cpp"

# Full-resolution face samples. These match the numbering shown in
# Lengyel's dissertation Figure 4.16:
#
# 6 -- 7 -- 8
# |    |    |
# 3 -- 4 -- 5
# |    |    |
# 0 -- 1 -- 2
#
# We use integer coordinates scaled so the full-resolution face spans 0..2.
FULL_FACE_POSITIONS = {
    0: (0, 0, 0),
    1: (1, 0, 0),
    2: (2, 0, 0),
    3: (0, 1, 0),
    4: (1, 1, 0),
    5: (2, 1, 0),
    6: (0, 2, 0),
    7: (1, 2, 0),
    8: (2, 2, 0),
}

# Half-resolution face samples. The signs at these four locations are derived
# from the matching full-resolution corner samples, as described in the
# dissertation:
#
# B -- C
# |    |
# 9 -- A
#
# 9 == 0, A == 2, B == 6, C == 8.
HALF_FACE_POSITIONS = {
    9:  (0, 0, 1),
    10: (2, 0, 1),  # A
    11: (0, 2, 1),  # B
    12: (2, 2, 1),  # C
}

HALF_TO_FULL_CORNER = {
    9: 0,
    10: 2,
    11: 6,
    12: 8,
}

# Synthetic center used only by this independent tetrahedralized construction.
# Its sign is derived from full-resolution sample 4. This is one reason this
# table is not a claim of compatibility with the official Transvoxel table.
CENTER_ID = 13
CENTER_POSITION = (1, 1, 0.5)
CENTER_SIGN_SOURCE = 4

SAMPLE_POSITIONS = {
    **FULL_FACE_POSITIONS,
    **HALF_FACE_POSITIONS,
    CENTER_ID: CENTER_POSITION,
}

# Boundary triangulation of the transition cell:
# - full-resolution face split into 2x2 quads, 8 triangles
# - half-resolution face split into 2 triangles
# - four lateral faces, each a 5-sided face triangulated into 3 triangles
#
# Every boundary triangle is connected to CENTER_ID, giving a tetrahedral fan.
# This is a simple, deterministic construction intended to create a table from
# first principles. It is deliberately documented so its origin is auditable.
BOUNDARY_TRIANGLES = [
    # Full-resolution face.
    (0, 1, 4), (0, 4, 3),
    (1, 2, 5), (1, 5, 4),
    (3, 4, 7), (3, 7, 6),
    (4, 5, 8), (4, 8, 7),

    # Half-resolution face.
    (9, 10, 12), (9, 12, 11),

    # y-min lateral face: front 0-1-2 to back 9-10.
    (0, 1, 9), (1, 10, 9), (1, 2, 10),

    # x-max lateral face: front 2-5-8 to back 10-12.
    (2, 5, 10), (5, 12, 10), (5, 8, 12),

    # y-max lateral face: front 8-7-6 to back 12-11.
    (8, 7, 12), (7, 11, 12), (7, 6, 11),

    # x-min lateral face: front 6-3-0 to back 11-9.
    (6, 3, 11), (3, 9, 11), (3, 0, 9),
]

TETRAHEDRA = [(a, b, c, CENTER_ID) for (a, b, c) in BOUNDARY_TRIANGLES]

# Case bits from the full-resolution samples. This follows the natural bit
# order for sample ids 0..8. The dissertation uses hexadecimal quantities shown
# in Figure 4.17; those are equivalent to 1 << sample_id for the numbering in
# Figure 4.16.
CASE_BITS = {i: (1 << i) for i in range(9)}


def sign_for_sample(case_index: int, sample_id: int) -> bool:
    """Return True when the sample is inside/negative."""
    if 0 <= sample_id <= 8:
        return (case_index & CASE_BITS[sample_id]) != 0
    if sample_id in HALF_TO_FULL_CORNER:
        return sign_for_sample(case_index, HALF_TO_FULL_CORNER[sample_id])
    if sample_id == CENTER_ID:
        return sign_for_sample(case_index, CENTER_SIGN_SOURCE)
    raise ValueError(f"unknown sample id {sample_id}")


def edge_key(a: int, b: int) -> Tuple[int, int]:
    """Canonical local edge key for an interpolated vertex."""
    if a == b:
        raise ValueError("edge cannot connect a sample to itself")
    return (a, b) if a < b else (b, a)


def add_vertex(
    key: Tuple[int, int],
    vertices: List[Tuple[int, int]],
    vertex_map: Dict[Tuple[int, int], int],
) -> int:
    if key in vertex_map:
        return vertex_map[key]
    vertex_map[key] = len(vertices)
    vertices.append(key)
    return vertex_map[key]


def polygon_for_tetra(case_index: int, tet: Sequence[int]) -> List[Tuple[int, int]]:
    """Return edge keys making the polygon for one tetrahedron.

    The returned list has 0, 3, or 4 edge-intersection vertices.
    """
    inside = [v for v in tet if sign_for_sample(case_index, v)]
    outside = [v for v in tet if not sign_for_sample(case_index, v)]

    if len(inside) == 0 or len(inside) == 4:
        return []

    if len(inside) == 1:
        i = inside[0]
        return [edge_key(i, o) for o in outside]

    if len(inside) == 3:
        o = outside[0]
        # Reverse order compared with the one-inside case.
        return [edge_key(i, o) for i in reversed(inside)]

    # Two inside and two outside: a quad. It is triangulated later.
    i0, i1 = inside
    o0, o1 = outside
    return [
        edge_key(i0, o0),
        edge_key(i0, o1),
        edge_key(i1, o1),
        edge_key(i1, o0),
    ]


def generate_case(case_index: int) -> Dict[str, object]:
    vertices: List[Tuple[int, int]] = []
    vertex_map: Dict[Tuple[int, int], int] = {}
    triangles: List[Tuple[int, int, int]] = []

    for tet in TETRAHEDRA:
        poly = polygon_for_tetra(case_index, tet)
        if not poly:
            continue

        ids = [add_vertex(k, vertices, vertex_map) for k in poly]

        if len(ids) == 3:
            if ids[0] != ids[1] and ids[1] != ids[2] and ids[2] != ids[0]:
                triangles.append((ids[0], ids[1], ids[2]))
        elif len(ids) == 4:
            # Quad split. Degenerate triangles are skipped.
            a, b, c, d = ids
            if len({a, b, c}) == 3:
                triangles.append((a, b, c))
            if len({a, c, d}) == 3:
                triangles.append((a, c, d))
        else:
            raise AssertionError("unexpected polygon length")

    return {
        "case": case_index,
        "inside_samples": [i for i in range(9) if sign_for_sample(case_index, i)],
        "vertices": [{"id": i, "samples": [a, b]} for i, (a, b) in enumerate(vertices)],
        "triangles": [{"vertices": list(t)} for t in triangles],
    }


def generate_tables() -> Dict[str, object]:
    cases = [generate_case(case_index) for case_index in range(512)]

    table = {
        "schema": SCHEMA,
        "license": LICENSE,
        "status": STATUS,
        "warning": (
            "Independent experimental transition-cell table generated by marching tetrahedra "
            "over a documented tetrahedral fan. Not a copied, translated, or bit-compatible "
            "version of Eric Lengyel's MIT-licensed Transvoxel.cpp tables."
        ),
        "sample_positions": [
            {
                "id": i,
                "position": list(SAMPLE_POSITIONS[i]),
                "kind": (
                    "full_resolution_face" if i <= 8 else
                    "half_resolution_face" if i <= 12 else
                    "synthetic_center"
                ),
            }
            for i in sorted(SAMPLE_POSITIONS)
        ],
        "half_resolution_corner_sign_sources": {
            str(k): v for k, v in sorted(HALF_TO_FULL_CORNER.items())
        },
        "synthetic_center_sign_source": CENTER_SIGN_SOURCE,
        "boundary_triangles": [list(t) for t in BOUNDARY_TRIANGLES],
        "tetrahedra": [list(t) for t in TETRAHEDRA],
        "case_bits": {str(k): v for k, v in CASE_BITS.items()},
        "cases": cases,
    }

    encoded = json.dumps(table, sort_keys=True, separators=(",", ":")).encode("utf-8")
    table["sha256_without_this_field"] = hashlib.sha256(encoded).hexdigest()
    return table


def flatten(table: Dict[str, object]) -> Dict[str, List[Tuple[int, ...]]]:
    vertex_pairs: List[Tuple[int, int]] = []
    triangles: List[Tuple[int, int, int]] = []
    vertex_start = [0]
    triangle_start = [0]

    for case in table["cases"]:
        for vertex in case["vertices"]:
            a, b = vertex["samples"]
            vertex_pairs.append((int(a), int(b)))
        for tri in case["triangles"]:
            a, b, c = tri["vertices"]
            triangles.append((int(a), int(b), int(c)))
        vertex_start.append(len(vertex_pairs))
        triangle_start.append(len(triangles))

    return {
        "vertex_pairs": vertex_pairs,
        "triangles": triangles,
        "vertex_start": vertex_start,
        "triangle_start": triangle_start,
    }


def c_array(name: str, ctype: str, values: Sequence[int], per_line: int = 12) -> str:
    lines = [f"static const {ctype} {name}[{len(values)}] = {{"]
    for i in range(0, len(values), per_line):
        chunk = ", ".join(str(v) for v in values[i:i + per_line])
        lines.append(f"    {chunk},")
    lines.append("};")
    return "\n".join(lines)


def emit_header(table: Dict[str, object]) -> str:
    flat = flatten(table)
    vertex_pairs = flat["vertex_pairs"]
    triangles = flat["triangles"]

    out: List[str] = []
    out.append("/* SPDX-License-Identifier: 0BSD */")
    out.append("/* Generated by tools/generate_transition.py. Do not edit by hand. */")
    out.append("/* Status: experimental_not_drop_in_transvoxel_cpp. */")
    out.append("#ifndef CLEANROOM_TRANSITION_TET_TABLES_H")
    out.append("#define CLEANROOM_TRANSITION_TET_TABLES_H")
    out.append("")
    out.append("#include <stdint.h>")
    out.append("")
    out.append("#define CLEANROOM_TRANSITION_CASE_COUNT 512")
    out.append("#define CLEANROOM_TRANSITION_SAMPLE_COUNT 14")
    out.append("#define CLEANROOM_TRANSITION_VERTEX_PAIR_COUNT %d" % len(vertex_pairs))
    out.append("#define CLEANROOM_TRANSITION_TRIANGLE_COUNT %d" % len(triangles))
    out.append("")
    out.append(c_array("transition_case_vertex_start", "uint16_t", flat["vertex_start"]))
    out.append("")
    out.append(c_array("transition_case_triangle_start", "uint16_t", flat["triangle_start"]))
    out.append("")
    out.append("static const uint8_t transition_vertex_pairs[%d][2] = {" % len(vertex_pairs))
    for a, b in vertex_pairs:
        out.append(f"    {{{a}, {b}}},")
    out.append("};")
    out.append("")
    out.append("static const uint8_t transition_triangles[%d][3] = {" % len(triangles))
    for a, b, c in triangles:
        out.append(f"    {{{a}, {b}, {c}}},")
    out.append("};")
    out.append("")
    out.append("#endif")
    out.append("")
    return "\n".join(out)


def d_array(name: str, dtype: str, values: Sequence[int], per_line: int = 12) -> str:
    lines = [f"immutable {dtype}[{len(values)}] {name} = ["]
    for i in range(0, len(values), per_line):
        chunk = ", ".join(str(v) for v in values[i:i + per_line])
        lines.append(f"    {chunk},")
    lines.append("];")
    return "\n".join(lines)


def emit_d(table: Dict[str, object]) -> str:
    flat = flatten(table)
    vertex_pairs = flat["vertex_pairs"]
    triangles = flat["triangles"]

    out: List[str] = []
    out.append("// SPDX-License-Identifier: 0BSD")
    out.append("// Generated by tools/generate_transition.py. Do not edit by hand.")
    out.append("// Status: experimental_not_drop_in_transvoxel_cpp.")
    out.append("module transition_tables;")
    out.append("")
    out.append("enum transitionCaseCount = 512;")
    out.append("enum transitionSampleCount = 14;")
    out.append("")
    out.append("struct Pair { ubyte a; ubyte b; }")
    out.append("struct Tri { ubyte a; ubyte b; ubyte c; }")
    out.append("")
    out.append(d_array("caseVertexStart", "ushort", flat["vertex_start"]))
    out.append("")
    out.append(d_array("caseTriangleStart", "ushort", flat["triangle_start"]))
    out.append("")
    out.append("immutable Pair[%d] vertexPairs = [" % len(vertex_pairs))
    for a, b in vertex_pairs:
        out.append(f"    Pair({a}, {b}),")
    out.append("];")
    out.append("")
    out.append("immutable Tri[%d] triangles = [" % len(triangles))
    for a, b, c in triangles:
        out.append(f"    Tri({a}, {b}, {c}),")
    out.append("];")
    out.append("")
    return "\n".join(out)


def verify_table(table: Dict[str, object]) -> List[str]:
    errors: List[str] = []
    if table.get("schema") != SCHEMA:
        errors.append("schema mismatch")

    cases = table.get("cases", [])
    if len(cases) != 512:
        errors.append("expected 512 cases")

    if cases:
        if cases[0]["triangles"]:
            errors.append("case 0 should contain no triangles")
        if cases[511]["triangles"]:
            errors.append("case 511 should contain no triangles")

    for case in cases:
        vertices = case["vertices"]
        triangles = case["triangles"]
        vertex_count = len(vertices)

        seen = set()
        for vertex in vertices:
            pair = tuple(vertex["samples"])
            if len(pair) != 2 or pair[0] == pair[1]:
                errors.append(f"case {case['case']}: invalid vertex pair {pair}")
            if pair in seen:
                errors.append(f"case {case['case']}: duplicate vertex pair {pair}")
            seen.add(pair)

        for tri in triangles:
            ids = tri["vertices"]
            if len(ids) != 3 or len(set(ids)) != 3:
                errors.append(f"case {case['case']}: degenerate triangle {ids}")
            for idx in ids:
                if not 0 <= idx < vertex_count:
                    errors.append(f"case {case['case']}: triangle references invalid vertex {idx}")

    return errors


def write_outputs(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    table = generate_tables()

    json_text = json.dumps(table, indent=2, sort_keys=True)
    (out_dir / "transition_tables.json").write_text(json_text + "\n", encoding="utf-8")
    (out_dir / "transition_tables.h").write_text(emit_header(table), encoding="utf-8")
    (out_dir / "transition_tables.d").write_text(emit_d(table), encoding="utf-8")

    errors = verify_table(table)
    if errors:
        raise SystemExit("\n".join(errors))

    print("generated:", out_dir)
    print("schema:", table["schema"])
    print("status:", table["status"])
    print("sha256:", table["sha256_without_this_field"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="generated", help="Output directory")
    parser.add_argument("--check", action="store_true", help="Generate in memory and run checks only")
    args = parser.parse_args()

    if args.check:
        table = generate_tables()
        errors = verify_table(table)
        if errors:
            raise SystemExit("\n".join(errors))
        print("ok")
        print("sha256:", table["sha256_without_this_field"])
        return

    write_outputs(Path(args.out))


if __name__ == "__main__":
    main()
