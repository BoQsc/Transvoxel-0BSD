#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Clean-room modified-Marching-Cubes regular-cell table generator.

The topology is derived from the public preferred-polarity face rule and
minimal boundary-loop fillings. It does not read or compare official lookup
table arrays.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
M3_DIR = ROOT / "research" / "official_topology" / "m3"
sys.path.insert(0, str(M3_DIR))
import m3_core as topology  # noqa: E402

SCHEMA = "boqsc.regular_tables.v1"
LICENSE = "0BSD"
STATUS = "clean_room_modified_marching_cubes_preferred_polarity"

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

FACES = [
    ("z_min", (0, 1, 3, 2)),
    ("z_max", (4, 6, 7, 5)),
    ("x_min", (0, 2, 6, 4)),
    ("x_max", (1, 5, 7, 3)),
    ("y_min", (0, 4, 5, 1)),
    ("y_max", (2, 3, 7, 6)),
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


def square_segments(
    case_index: int,
    square: Sequence[int],
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    crossings = []
    for index, sample_id in enumerate(square):
        next_sample = square[(index + 1) % 4]
        if (
            sign_for_sample(case_index, sample_id)
            != sign_for_sample(case_index, next_sample)
        ):
            crossings.append(edge_key(sample_id, next_sample))
    if not crossings:
        return []
    if len(crossings) == 2:
        return [topology.segment_key(crossings[0], crossings[1])]
    if len(crossings) != 4:
        raise AssertionError("square must have zero, two, or four crossings")
    # Preferred polarity: connect crossings on adjacent edges sharing an
    # inside corner.
    result = []
    for index, sample_id in enumerate(square):
        if sign_for_sample(case_index, sample_id):
            result.append(topology.segment_key(
                edge_key(square[(index - 1) % 4], sample_id),
                edge_key(sample_id, square[(index + 1) % 4]),
            ))
    return sorted(result)


def boundary_segments(
    case_index: int,
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    return [
        segment
        for _name, square in FACES
        for segment in square_segments(case_index, square)
    ]


def edge_midpoint(edge: Tuple[int, int]) -> Tuple[float, float, float]:
    a = SAMPLE_POSITIONS[edge[0]]
    b = SAMPLE_POSITIONS[edge[1]]
    return (
        (a[0] + b[0]) * 0.5,
        (a[1] + b[1]) * 0.5,
        (a[2] + b[2]) * 0.5,
    )


def sub(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sample_value(case_index: int, sample_id: int) -> float:
    return -1.0 if sign_for_sample(case_index, sample_id) else 1.0


def regular_gradient(
    case_index: int,
    position: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    x, y, z = position
    f000 = sample_value(case_index, 0)
    f100 = sample_value(case_index, 1)
    f010 = sample_value(case_index, 2)
    f110 = sample_value(case_index, 3)
    f001 = sample_value(case_index, 4)
    f101 = sample_value(case_index, 5)
    f011 = sample_value(case_index, 6)
    f111 = sample_value(case_index, 7)
    dx = (
        (f100 - f000) * (1.0 - y) * (1.0 - z)
        + (f110 - f010) * y * (1.0 - z)
        + (f101 - f001) * (1.0 - y) * z
        + (f111 - f011) * y * z
    )
    dy = (
        (f010 - f000) * (1.0 - x) * (1.0 - z)
        + (f110 - f100) * x * (1.0 - z)
        + (f011 - f001) * (1.0 - x) * z
        + (f111 - f101) * x * z
    )
    dz = (
        (f001 - f000) * (1.0 - x) * (1.0 - y)
        + (f101 - f100) * x * (1.0 - y)
        + (f011 - f010) * (1.0 - x) * y
        + (f111 - f110) * x * y
    )
    return (dx, dy, dz)


def orient_components(
    case_index: int,
    triangles: Sequence[
        Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]
    ],
) -> List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
    result = [list(triangle) for triangle in triangles]
    edge_uses = defaultdict(list)
    for triangle_id, triangle in enumerate(result):
        for a, b in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            key = topology.segment_key(a, b)
            edge_uses[key].append((triangle_id, a, b))

    flips: List[bool | None] = [None] * len(result)
    components = []
    for start in range(len(result)):
        if flips[start] is not None:
            continue
        flips[start] = False
        pending = [start]
        component = []
        while pending:
            triangle_id = pending.pop()
            component.append(triangle_id)
            triangle = result[triangle_id]
            for a, b in (
                (triangle[0], triangle[1]),
                (triangle[1], triangle[2]),
                (triangle[2], triangle[0]),
            ):
                key = topology.segment_key(a, b)
                for neighbor_id, neighbor_a, neighbor_b in edge_uses[key]:
                    if neighbor_id == triangle_id:
                        continue
                    same = a == neighbor_a and b == neighbor_b
                    neighbor_flip = bool(flips[triangle_id]) ^ same
                    if flips[neighbor_id] is None:
                        flips[neighbor_id] = neighbor_flip
                        pending.append(neighbor_id)
                    elif flips[neighbor_id] != neighbor_flip:
                        raise ValueError(
                            f"case {case_index}: non-orientable component"
                        )
        components.append(component)
    for triangle_id, flip in enumerate(flips):
        if flip:
            result[triangle_id][1], result[triangle_id][2] = (
                result[triangle_id][2],
                result[triangle_id][1],
            )

    for component in components:
        score = 0.0
        for triangle_id in component:
            points = [
                edge_midpoint(vertex) for vertex in result[triangle_id]
            ]
            normal = cross(
                sub(points[1], points[0]),
                sub(points[2], points[0]),
            )
            centroid = (
                sum(point[0] for point in points) / 3.0,
                sum(point[1] for point in points) / 3.0,
                sum(point[2] for point in points) / 3.0,
            )
            score += dot(normal, regular_gradient(case_index, centroid))
        if abs(score) <= 1.0e-12:
            raise ValueError(f"case {case_index}: cannot orient component")
        if score < 0.0:
            for triangle_id in component:
                result[triangle_id][1], result[triangle_id][2] = (
                    result[triangle_id][2],
                    result[triangle_id][1],
                )
    return [
        (triangle[0], triangle[1], triangle[2])
        for triangle in result
    ]


def generate_case(case_index: int) -> Dict[str, object]:
    segments = boundary_segments(case_index)
    old_positions = topology.SAMPLE_POSITIONS
    topology.SAMPLE_POSITIONS = {
        sample_id: tuple(float(value) for value in position)
        for sample_id, position in SAMPLE_POSITIONS.items()
    }
    try:
        loop_report = topology.trace_boundary_loops(segments)
        if loop_report["status"] != "PASS":
            raise ValueError(
                f"case {case_index}: boundary loop derivation failed"
            )
        loops = loop_report["loops"]
        edge_triangles, method = topology.select_nonintersecting_loop_fills(
            loops
        )
        if edge_triangles is None:
            raise ValueError(f"case {case_index}: triangulation failed")
        validation = topology.validate_triangle_complex(
            edge_triangles,
            segments,
        )
        if validation["status"] != "PASS":
            raise ValueError(
                f"case {case_index}: triangle validation failed {validation}"
            )
    finally:
        topology.SAMPLE_POSITIONS = old_positions
    edge_triangles = orient_components(case_index, edge_triangles)
    vertices = sorted({
        vertex for triangle in edge_triangles for vertex in triangle
    })
    vertex_map = {
        vertex: vertex_id for vertex_id, vertex in enumerate(vertices)
    }
    triangles = [
        tuple(vertex_map[vertex] for vertex in triangle)
        for triangle in edge_triangles
    ]
    return {
        "case": case_index,
        "inside_samples": [i for i in range(8) if sign_for_sample(case_index, i)],
        "vertices": [{"id": i, "samples": [a, b]} for i, (a, b) in enumerate(vertices)],
        "triangles": [{"vertices": list(t)} for t in triangles],
        "boundary_segments": [
            [list(segment[0]), list(segment[1])] for segment in segments
        ],
        "boundary_loops": [
            [list(vertex) for vertex in loop] for loop in loops
        ],
        "triangulation_method": method,
    }


def generate_tables() -> Dict[str, object]:
    cases = [generate_case(i) for i in range(256)]
    table = {
        "schema": SCHEMA,
        "license": LICENSE,
        "status": STATUS,
        "warning": (
            "Clean-room modified-Marching-Cubes behavior derived from public "
            "preferred-polarity face rules. Not copied from or compared "
            "against official lookup-table arrays."
        ),
        "sample_positions": [{"id": i, "position": list(SAMPLE_POSITIONS[i])} for i in sorted(SAMPLE_POSITIONS)],
        "faces": [
            {"name": name, "samples": list(samples)}
            for name, samples in FACES
        ],
        "face_rule": (
            "Preferred polarity: on an ambiguous face, connect crossings on "
            "adjacent edges sharing an inside corner."
        ),
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
    out.append("/* Status: clean_room_modified_marching_cubes_preferred_polarity. */")
    out.append("#ifndef CLEANROOM_REGULAR_TABLES_H")
    out.append("#define CLEANROOM_REGULAR_TABLES_H")
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
    out.append("// Status: clean_room_modified_marching_cubes_preferred_polarity.")
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
