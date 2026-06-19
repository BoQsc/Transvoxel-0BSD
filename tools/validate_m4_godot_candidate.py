#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the M4 candidate table in the Godot-generated data path.

This is a Godot-stage-compatible validator. It proves that the M4 candidate
table has been synced into `godot/generated/` and that the table satisfies the
same non-visual seam-metrics shape expected from a headless Godot stage.

It does not execute Godot and does not claim official Transvoxel.cpp
equivalence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TABLE = ROOT / "generated" / "official_topology_candidate_tables.json"
GODOT_TABLE = ROOT / "godot" / "generated" / "official_topology_candidate_tables.json"
REPORT = ROOT / "validation" / "m4_godot_candidate_report.json"

GRID_SIZE = 8
SEED_COUNT = 12
FIELDS = ["plane_x", "plane_y", "diagonal", "circle", "saddle", "hash_noise", "wavy"]

Edge = Tuple[int, int]
Segment = Tuple[Edge, Edge]
Vec3 = Tuple[float, float, float]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def edge_key(a: int, b: int) -> Edge:
    if a == b:
        raise ValueError("degenerate sample edge")
    return (a, b) if a < b else (b, a)


def segment_key(a: Edge, b: Edge) -> Segment:
    if a == b:
        raise ValueError("degenerate boundary segment")
    return (a, b) if a < b else (b, a)


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length2(a: Vec3) -> float:
    return a[0] * a[0] + a[1] * a[1] + a[2] * a[2]


def sample_positions(table: Dict[str, Any]) -> Dict[int, Vec3]:
    out: Dict[int, Vec3] = {}
    for record in table.get("samples", []):
        pos = record.get("position", [])
        out[int(record.get("id", -1))] = (float(pos[0]), float(pos[1]), float(pos[2]))
    return out


def edge_midpoint(edge: Edge, positions: Dict[int, Vec3]) -> Vec3:
    a, b = edge
    pa = positions[a]
    pb = positions[b]
    return (
        (pa[0] + pb[0]) * 0.5,
        (pa[1] + pb[1]) * 0.5,
        (pa[2] + pb[2]) * 0.5,
    )


def triangle_area2(a: Vec3, b: Vec3, c: Vec3) -> float:
    return length2(cross(vsub(b, a), vsub(c, a)))


def case_vertex_edges(case: Dict[str, Any]) -> List[Edge]:
    return [
        edge_key(int(vertex["samples"][0]), int(vertex["samples"][1]))
        for vertex in case.get("vertices", [])
    ]


def boundary_segments(case: Dict[str, Any]) -> List[Segment]:
    vertex_edges = case_vertex_edges(case)
    counts: Dict[Tuple[int, int], int] = {}
    for triangle in case.get("triangles", []):
        ids = [int(value) for value in triangle.get("vertices", [])]
        if len(ids) != 3:
            continue
        for a, b in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            key = (a, b) if a < b else (b, a)
            counts[key] = counts.get(key, 0) + 1
    out: List[Segment] = []
    for (a, b), count in counts.items():
        if count == 1 and 0 <= a < len(vertex_edges) and 0 <= b < len(vertex_edges):
            out.append(segment_key(vertex_edges[a], vertex_edges[b]))
    out.sort()
    return out


def coord_equal(a: float, b: float) -> bool:
    return abs(a - b) <= 0.000001


def point_on_face(point: Vec3, face: str) -> bool:
    if face == "x_min":
        return coord_equal(point[0], 0.0)
    if face == "x_max":
        return coord_equal(point[0], 2.0)
    if face == "y_min":
        return coord_equal(point[1], 0.0)
    if face == "y_max":
        return coord_equal(point[1], 2.0)
    raise ValueError("unknown face: " + face)


def quantize(value: float) -> int:
    return int(round(value * 2.0))


def project_face_point(point: Vec3, face: str) -> Tuple[int, int]:
    if face.startswith("x_"):
        return (quantize(point[1]), quantize(point[2]))
    return (quantize(point[0]), quantize(point[2]))


def face_fingerprint(
    case: Dict[str, Any],
    face: str,
    positions: Dict[int, Vec3],
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    out: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    for a_edge, b_edge in boundary_segments(case):
        a = edge_midpoint(a_edge, positions)
        b = edge_midpoint(b_edge, positions)
        if point_on_face(a, face) and point_on_face(b, face):
            pa = project_face_point(a, face)
            pb = project_face_point(b, face)
            out.append((pa, pb) if pa <= pb else (pb, pa))
    out.sort()
    return out


def field_inside(field_id: int, x: int, y: int, seed: int) -> bool:
    if field_id == 0:
        return x < 5 + (seed % 3)
    if field_id == 1:
        return y < 4 + (seed % 4)
    if field_id == 2:
        return x + y < 8 + (seed % 5)
    if field_id == 3:
        cx = 6 + (seed % 3)
        cy = 6 + ((seed // 2) % 3)
        r = 5 + (seed % 2)
        return (x - cx) * (x - cx) + (y - cy) * (y - cy) < r * r
    if field_id == 4:
        return (x - 6) * (x - 6) - (y - 6) * (y - 6) + seed - 2 < 0
    if field_id == 5:
        n = ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        n = (n ^ (n >> 16)) & 0xFFFFFFFF
        return (n & 1) != 0
    return ((x + seed) % 7) + ((y * 3 + seed) % 11) < 8


def case_for_cell(field_id: int, cx: int, cy: int, seed: int) -> int:
    case_index = 0
    sample_id = 0
    for sy in range(3):
        for sx in range(3):
            gx = cx * 2 + sx
            gy = cy * 2 + sy
            if field_inside(field_id, gx, gy, seed):
                case_index |= 1 << sample_id
            sample_id += 1
    return case_index


def validate_strips(cases: Sequence[Dict[str, Any]], positions: Dict[int, Vec3]) -> Dict[str, Any]:
    failures: List[Dict[str, Any]] = []
    shared_faces = 0
    builds = 0
    total_vertices = 0
    total_triangles = 0
    for field_id, field_name in enumerate(FIELDS):
        for seed in range(SEED_COUNT):
            grid: List[List[int]] = []
            for y in range(GRID_SIZE):
                row: List[int] = []
                for x in range(GRID_SIZE):
                    case_index = case_for_cell(field_id, x, y, seed)
                    row.append(case_index)
                    case = cases[case_index]
                    total_vertices += int(case.get("vertex_count", len(case.get("vertices", []))))
                    total_triangles += int(case.get("triangle_count", len(case.get("triangles", []))))
                    builds += 1
                grid.append(row)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE - 1):
                    left = cases[grid[y][x]]
                    right = cases[grid[y][x + 1]]
                    shared_faces += 1
                    if face_fingerprint(left, "x_max", positions) != face_fingerprint(right, "x_min", positions):
                        if len(failures) < 100:
                            failures.append({
                                "field": field_name,
                                "seed": seed,
                                "cell_a": [x, y],
                                "cell_b": [x + 1, y],
                                "face_a": "x_max",
                                "face_b": "x_min",
                            })
            for y in range(GRID_SIZE - 1):
                for x in range(GRID_SIZE):
                    lower = cases[grid[y][x]]
                    upper = cases[grid[y + 1][x]]
                    shared_faces += 1
                    if face_fingerprint(lower, "y_max", positions) != face_fingerprint(upper, "y_min", positions):
                        if len(failures) < 100:
                            failures.append({
                                "field": field_name,
                                "seed": seed,
                                "cell_a": [x, y],
                                "cell_b": [x, y + 1],
                                "face_a": "y_max",
                                "face_b": "y_min",
                            })
    return {
        "status": "PASS" if not failures else "FAIL",
        "fields": len(FIELDS),
        "field_names": FIELDS,
        "seeds": SEED_COUNT,
        "grid": GRID_SIZE,
        "builds": builds,
        "shared_faces": shared_faces,
        "failures": len(failures),
        "failure_examples": failures,
        "total_vertices": total_vertices,
        "total_triangles": total_triangles,
    }


def validate_triangles(cases: Iterable[Dict[str, Any]], positions: Dict[int, Vec3]) -> Dict[str, Any]:
    invalid = 0
    degenerate = 0
    total = 0
    for case in cases:
        vertex_edges = case_vertex_edges(case)
        for triangle in case.get("triangles", []):
            ids = [int(value) for value in triangle.get("vertices", [])]
            total += 1
            if len(ids) != 3:
                invalid += 1
                continue
            if any(index < 0 or index >= len(vertex_edges) for index in ids):
                invalid += 1
                continue
            if len(set(ids)) != 3:
                degenerate += 1
                continue
            pts = [edge_midpoint(vertex_edges[index], positions) for index in ids]
            if triangle_area2(pts[0], pts[1], pts[2]) <= 0.0000001:
                degenerate += 1
    return {
        "status": "PASS" if invalid == 0 and degenerate == 0 else "FAIL",
        "invalid_triangles": invalid,
        "degenerate_triangles": degenerate,
        "total_triangles": total,
    }


def validate_table(table: Dict[str, Any]) -> Dict[str, Any]:
    cases = list(table.get("cases", []))
    positions = sample_positions(table)
    stats = table.get("statistics", {})
    issues: List[str] = []
    if table.get("schema") != "boqsc.transvoxel.official_topology.m4.runtime_candidate.v1":
        issues.append("unexpected schema")
    if len(cases) != 512:
        issues.append("case count is not 512")
    if int(stats.get("research_class_count", 0)) != 73:
        issues.append("research class count is not 73")
    if len(positions) != 13:
        issues.append("sample count is not 13")
    if int(stats.get("total_triangles", 0)) != 2640:
        issues.append("total triangle count is not 2640")
    if int(stats.get("total_vertex_pairs", 0)) != 4096:
        issues.append("total vertex-pair count is not 4096")
    triangles = validate_triangles(cases, positions)
    strips = validate_strips(cases, positions)
    if triangles["status"] != "PASS":
        issues.append("triangle validation failed")
    if strips["status"] != "PASS":
        issues.append("strip seam validation failed")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "case_count": len(cases),
        "sample_count": len(positions),
        "statistics": stats,
        "triangles": triangles,
        "strips": strips,
        "seam_open_edges": strips["failures"],
        "invalid_triangles": triangles["invalid_triangles"],
        "degenerate_triangles": triangles["degenerate_triangles"],
    }


def main() -> int:
    missing = [
        str(path.relative_to(ROOT))
        for path in [CANONICAL_TABLE, GODOT_TABLE]
        if not path.exists()
    ]
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_godot_candidate_report.v1",
        "status": "FAIL",
        "meaning": (
            "Validates the M4 candidate table in the Godot generated-data path "
            "using the same non-visual metrics shape expected from the M10 "
            "Godot stage. This does not execute Godot."
        ),
        "godot_runtime_executed": False,
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "missing": missing,
    }
    if missing:
        write_json(REPORT, report)
        print("M4 Godot candidate:", report["status"])
        return 1

    canonical_bytes = CANONICAL_TABLE.read_bytes()
    godot_bytes = GODOT_TABLE.read_bytes()
    table = read_json(GODOT_TABLE)
    validation = validate_table(table)
    ok = canonical_bytes == godot_bytes and validation["status"] == "PASS"
    report.update({
        "status": "PASS_M4_GODOT_STYLE_CANDIDATE_METRICS" if ok else "FAIL_M4_GODOT_STYLE_CANDIDATE_METRICS",
        "m4_table_synced_to_godot": canonical_bytes == godot_bytes,
        "canonical_table": "generated/official_topology_candidate_tables.json",
        "godot_table": "godot/generated/official_topology_candidate_tables.json",
        "metrics_output_equivalent": "godot/validation/05_m4_candidate_metrics/m4_candidate_metrics.json",
        "validation": validation,
    })
    write_json(REPORT, report)
    print("M4 Godot candidate:", report["status"])
    print(
        "m4 godot-style builds={builds} shared_faces={shared} seam_open_edges={failures}".format(
            builds=validation["strips"]["builds"],
            shared=validation["strips"]["shared_faces"],
            failures=validation["strips"]["failures"],
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
