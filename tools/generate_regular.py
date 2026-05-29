#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Clean-room regular-cell table generator using marching tetrahedra.

This is included so the transition-cell experiment has a matching regular-cell
baseline. It is not a copy of any Marching Cubes or Transvoxel lookup table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SCHEMA = "boqsc.regular_tables.v1"
LICENSE = "0BSD"
STATUS = "experimental_regular_marching_tetrahedra_not_marching_cubes"

SAMPLE_POSITIONS = {
    0: (0, 0, 0),
    1: (1, 0, 0),
    2: (0, 1, 0),
    3: (1, 1, 0),
    4: (0, 0, 1),
    5: (1, 0, 1),
    6: (0, 1, 1),
    7: (1, 1, 1),
}

# Six tetrahedra around the long diagonal 0 -> 7.
TETRAHEDRA = [
    (0, 1, 3, 7),
    (0, 3, 2, 7),
    (0, 2, 6, 7),
    (0, 6, 4, 7),
    (0, 4, 5, 7),
    (0, 5, 1, 7),
]

CASE_BITS = {i: (1 << i) for i in range(8)}


def sign_for_sample(case_index: int, sample_id: int) -> bool:
    if not 0 <= sample_id < 8:
        raise ValueError("sample id out of range")
    return (case_index & CASE_BITS[sample_id]) != 0


def edge_key(a: int, b: int) -> Tuple[int, int]:
    if a == b:
        raise ValueError("edge cannot connect a sample to itself")
    return (a, b) if a < b else (b, a)


def add_vertex(key: Tuple[int, int], vertices: List[Tuple[int, int]], vertex_map: Dict[Tuple[int, int], int]) -> int:
    if key in vertex_map:
        return vertex_map[key]
    vertex_map[key] = len(vertices)
    vertices.append(key)
    return vertex_map[key]


def polygon_for_tetra(case_index: int, tet: Sequence[int]) -> List[Tuple[int, int]]:
    inside = [v for v in tet if sign_for_sample(case_index, v)]
    outside = [v for v in tet if not sign_for_sample(case_index, v)]
    if len(inside) == 0 or len(inside) == 4:
        return []
    if len(inside) == 1:
        i = inside[0]
        return [edge_key(i, o) for o in outside]
    if len(inside) == 3:
        o = outside[0]
        return [edge_key(i, o) for i in reversed(inside)]
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
            if len(set(ids)) == 3:
                triangles.append((ids[0], ids[1], ids[2]))
        elif len(ids) == 4:
            a, b, c, d = ids
            if len({a, b, c}) == 3:
                triangles.append((a, b, c))
            if len({a, c, d}) == 3:
                triangles.append((a, c, d))
        else:
            raise AssertionError("unexpected polygon length")
    return {
        "case": case_index,
        "inside_samples": [i for i in range(8) if sign_for_sample(case_index, i)],
        "vertices": [{"id": i, "samples": [a, b]} for i, (a, b) in enumerate(vertices)],
        "triangles": [{"vertices": list(t)} for t in triangles],
    }


def generate_tables() -> Dict[str, object]:
    cases = [generate_case(i) for i in range(256)]
    table = {
        "schema": SCHEMA,
        "license": LICENSE,
        "status": STATUS,
        "warning": "Independent regular-cell marching-tetrahedra table. Not a copied or compatible Marching Cubes table.",
        "sample_positions": [{"id": i, "position": list(SAMPLE_POSITIONS[i])} for i in sorted(SAMPLE_POSITIONS)],
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
    return {"vertex_pairs": vertex_pairs, "triangles": triangles, "vertex_start": vertex_start, "triangle_start": triangle_start}


def c_array(name: str, ctype: str, values: Sequence[int], per_line: int = 12) -> str:
    lines = [f"static const {ctype} {name}[{len(values)}] = {{"]
    for i in range(0, len(values), per_line):
        lines.append("    " + ", ".join(str(v) for v in values[i:i + per_line]) + ",")
    lines.append("};")
    return "\n".join(lines)


def emit_header(table: Dict[str, object]) -> str:
    flat = flatten(table)
    vertex_pairs = flat["vertex_pairs"]
    triangles = flat["triangles"]
    out: List[str] = []
    out.append("/* SPDX-License-Identifier: 0BSD */")
    out.append("/* Generated by tools/generate_regular.py. Do not edit by hand. */")
    out.append("/* Status: experimental_regular_marching_tetrahedra_not_marching_cubes. */")
    out.append("#ifndef CLEANROOM_REGULAR_TET_TABLES_H")
    out.append("#define CLEANROOM_REGULAR_TET_TABLES_H")
    out.append("")
    out.append("#include <stdint.h>")
    out.append("")
    out.append("#define CLEANROOM_REGULAR_CASE_COUNT 256")
    out.append("#define CLEANROOM_REGULAR_SAMPLE_COUNT 8")
    out.append("#define CLEANROOM_REGULAR_VERTEX_PAIR_COUNT %d" % len(vertex_pairs))
    out.append("#define CLEANROOM_REGULAR_TRIANGLE_COUNT %d" % len(triangles))
    out.append("")
    out.append(c_array("regular_case_vertex_start", "uint16_t", flat["vertex_start"]))
    out.append("")
    out.append(c_array("regular_case_triangle_start", "uint16_t", flat["triangle_start"]))
    out.append("")
    out.append("static const uint8_t regular_vertex_pairs[%d][2] = {" % len(vertex_pairs))
    for a, b in vertex_pairs:
        out.append(f"    {{{a}, {b}}},")
    out.append("};")
    out.append("")
    out.append("static const uint8_t regular_triangles[%d][3] = {" % len(triangles))
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
        lines.append("    " + ", ".join(str(v) for v in values[i:i + per_line]) + ",")
    lines.append("];")
    return "\n".join(lines)


def emit_d(table: Dict[str, object]) -> str:
    flat = flatten(table)
    vertex_pairs = flat["vertex_pairs"]
    triangles = flat["triangles"]
    out: List[str] = []
    out.append("// SPDX-License-Identifier: 0BSD")
    out.append("// Generated by tools/generate_regular.py. Do not edit by hand.")
    out.append("// Status: experimental_regular_marching_tetrahedra_not_marching_cubes.")
    out.append("module regular_tables;")
    out.append("")
    out.append("enum regularCaseCount = 256;")
    out.append("enum regularSampleCount = 8;")
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
    if len(cases) != 256:
        errors.append("expected 256 cases")
    if cases:
        if cases[0]["triangles"]:
            errors.append("case 0 should contain no triangles")
        if cases[255]["triangles"]:
            errors.append("case 255 should contain no triangles")
    for case in cases:
        seen = set()
        vertex_count = len(case["vertices"])
        for vertex in case["vertices"]:
            pair = tuple(vertex["samples"])
            if len(pair) != 2 or pair[0] == pair[1]:
                errors.append(f"case {case['case']}: invalid vertex pair {pair}")
            if pair in seen:
                errors.append(f"case {case['case']}: duplicate vertex pair {pair}")
            seen.add(pair)
        for tri in case["triangles"]:
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
    (out_dir / "regular_tables.json").write_text(json.dumps(table, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "regular_tables.h").write_text(emit_header(table), encoding="utf-8")
    (out_dir / "regular_tables.d").write_text(emit_d(table), encoding="utf-8")
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
