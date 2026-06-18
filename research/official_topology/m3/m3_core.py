#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Shared clean-room geometry and topology logic for official-topology M3.

This module uses only the public transition-cell sample layout, the D4 symmetry
action, preferred-polarity face contours, and the documented lateral-face
contour rules. It does not read or compare official Transvoxel table arrays.
"""
from __future__ import annotations

import itertools
import math
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

CASE_MASK = 0x1FF

EdgeKey = Tuple[int, int]
SegmentKey = Tuple[EdgeKey, EdgeKey]
Triangle = Tuple[EdgeKey, EdgeKey, EdgeKey]
Vec2 = Tuple[float, float]
Vec3 = Tuple[float, float, float]

FULL_POSITIONS: Dict[int, Vec3] = {
    i: (float(i % 3), float(i // 3), 0.0) for i in range(9)
}
HALF_POSITIONS: Dict[int, Vec3] = {
    9: (0.0, 0.0, 1.0),
    10: (2.0, 0.0, 1.0),
    11: (0.0, 2.0, 1.0),
    12: (2.0, 2.0, 1.0),
}
SAMPLE_POSITIONS = {**FULL_POSITIONS, **HALF_POSITIONS}
HALF_TO_FULL = {9: 0, 10: 2, 11: 6, 12: 8}

FULL_QUADRANTS: Tuple[Tuple[str, Tuple[int, int, int, int]], ...] = (
    ("full_q00", (0, 1, 4, 3)),
    ("full_q10", (1, 2, 5, 4)),
    ("full_q01", (3, 4, 7, 6)),
    ("full_q11", (4, 5, 8, 7)),
)
HALF_FACE = ("half", (9, 10, 12, 11))
LATERAL_FACES: Tuple[
    Tuple[str, Tuple[int, int, int], Tuple[int, int]], ...
] = (
    ("lateral_y_min", (0, 1, 2), (9, 10)),
    ("lateral_x_max", (2, 5, 8), (10, 12)),
    ("lateral_y_max", (8, 7, 6), (12, 11)),
    ("lateral_x_min", (6, 3, 0), (11, 9)),
)

GRID_COORDS = [(i % 3, i // 3) for i in range(9)]
GRID_INDEX = {(x, y): y * 3 + x for x in range(3) for y in range(3)}


def edge_key(a: int, b: int) -> EdgeKey:
    if a == b:
        raise ValueError("edge endpoints must differ")
    return (a, b) if a < b else (b, a)


def segment_key(a: EdgeKey, b: EdgeKey) -> SegmentKey:
    if a == b:
        raise ValueError("segment endpoints must differ")
    return (a, b) if a < b else (b, a)


def triangle_key(a: EdgeKey, b: EdgeKey, c: EdgeKey) -> Triangle:
    return (a, b, c)


def sample_sign(case_index: int, sample_id: int) -> int:
    source = HALF_TO_FULL.get(sample_id, sample_id)
    return (case_index >> source) & 1


def transform_coord(x: int, y: int, transform: int) -> Tuple[int, int]:
    if transform >= 4:
        x = 2 - x
    for _ in range(transform % 4):
        x, y = 2 - y, x
    return x, y


D4_PERMUTATIONS: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(GRID_INDEX[transform_coord(x, y, transform)] for x, y in GRID_COORDS)
    for transform in range(8)
)


def apply_permutation(case_index: int, permutation: Sequence[int]) -> int:
    result = 0
    for old_index, new_index in enumerate(permutation):
        if (case_index >> old_index) & 1:
            result |= 1 << new_index
    return result


def d4_orbit(case_index: int) -> Tuple[int, ...]:
    return tuple(sorted({apply_permutation(case_index, p) for p in D4_PERMUTATIONS}))


def square_is_ambiguous(case_index: int, square: Sequence[int]) -> bool:
    bits = [sample_sign(case_index, sample_id) for sample_id in square]
    return bits[0] == bits[2] and bits[1] == bits[3] and bits[0] != bits[1]


def ambiguity_flags(case_index: int) -> Dict[str, object]:
    full_names = [
        name for name, square in FULL_QUADRANTS
        if square_is_ambiguous(case_index, square)
    ]
    half = square_is_ambiguous(case_index, HALF_FACE[1])
    return {
        "full_resolution_quadrants": full_names,
        "has_full_resolution_ambiguity": bool(full_names),
        "has_half_resolution_ambiguity": half,
        "has_any_ambiguity": bool(full_names) or half,
    }


def derive_research_classes() -> Dict[str, object]:
    """Derive the 51 + 18 + 4 clean-room research partition.

    The numeric IDs are local research IDs. They are not official class IDs.
    """
    seen_orbits = set()
    base_orbits: List[Tuple[int, Tuple[int, ...]]] = []
    for case_index in range(512):
        orbit = d4_orbit(case_index)
        orbit_key = orbit
        if orbit_key in seen_orbits:
            continue
        seen_orbits.add(orbit_key)
        if case_index.bit_count() <= 4:
            base_orbits.append((min(orbit), orbit))
    base_orbits.sort(key=lambda item: (item[0].bit_count(), item[0]))

    classes: List[Dict[str, object]] = []
    split_full: List[Tuple[int, Tuple[int, ...], int]] = []
    split_half: List[Tuple[int, Tuple[int, ...], int]] = []

    for base_id, (representative, orbit) in enumerate(base_orbits):
        flags = ambiguity_flags(representative)
        has_full = bool(flags["has_full_resolution_ambiguity"])
        has_half = bool(flags["has_half_resolution_ambiguity"])
        cases = set(orbit)
        if not has_full and not has_half:
            cases.update(case ^ CASE_MASK for case in orbit)
            kind = "base_with_inversion"
        else:
            kind = "base_without_inversion"
            target = split_full if has_full else split_half
            target.append((representative, orbit, base_id))
        classes.append({
            "research_class_id": base_id,
            "kind": kind,
            "representative_case": representative,
            "cases": sorted(cases),
            "class_size": len(cases),
            "representative_inside_count": representative.bit_count(),
            "ambiguity": flags,
            "inverse_research_class_id": None,
            "source_base_research_class_id": base_id,
        })

    for kind, split in (
        ("inverse_split_full_resolution_ambiguity", split_full),
        ("inverse_split_half_resolution_only_ambiguity", split_half),
    ):
        for representative, orbit, base_id in split:
            inverse_cases = sorted(case ^ CASE_MASK for case in orbit)
            inverse_id = len(classes)
            inverse_representative = min(inverse_cases)
            classes[base_id]["inverse_research_class_id"] = inverse_id
            classes.append({
                "research_class_id": inverse_id,
                "kind": kind,
                "representative_case": inverse_representative,
                "cases": inverse_cases,
                "class_size": len(inverse_cases),
                "representative_inside_count": inverse_representative.bit_count(),
                "ambiguity": ambiguity_flags(inverse_representative),
                "inverse_research_class_id": base_id,
                "source_base_research_class_id": base_id,
            })

    case_to_class: List[Optional[int]] = [None] * 512
    overlap_cases: List[int] = []
    for record in classes:
        class_id = int(record["research_class_id"])
        for case_index in record["cases"]:  # type: ignore[union-attr]
            case_index = int(case_index)
            if case_to_class[case_index] is not None:
                overlap_cases.append(case_index)
            case_to_class[case_index] = class_id

    missing_cases = [i for i, class_id in enumerate(case_to_class) if class_id is None]
    size_histogram = Counter(int(record["class_size"]) for record in classes)
    return {
        "schema": "boqsc.transvoxel.official_topology.m3.class_partition.v1",
        "status": (
            "PASS_DERIVED_73_RESEARCH_CLASSES_OFFICIAL_IDS_NOT_PROVEN"
            if len(classes) == 73 and not overlap_cases and not missing_cases
            else "FAIL_CLASS_PARTITION"
        ),
        "research_class_count": len(classes),
        "base_class_count": len(base_orbits),
        "full_resolution_inverse_split_count": len(split_full),
        "half_resolution_only_inverse_split_count": len(split_half),
        "case_count": sum(int(record["class_size"]) for record in classes),
        "missing_cases": missing_cases,
        "overlap_cases": sorted(set(overlap_cases)),
        "class_size_histogram": {
            str(size): count for size, count in sorted(size_histogram.items())
        },
        "case_to_research_class": [int(x) if x is not None else -1 for x in case_to_class],
        "classes": classes,
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangulation_equivalence": "NOT_PROVEN",
    }


def square_segments(case_index: int, square: Sequence[int]) -> List[SegmentKey]:
    crossings: List[EdgeKey] = []
    for i in range(4):
        a = square[i]
        b = square[(i + 1) % 4]
        if sample_sign(case_index, a) != sample_sign(case_index, b):
            crossings.append(edge_key(a, b))
    if not crossings:
        return []
    if len(crossings) == 2:
        return [segment_key(crossings[0], crossings[1])]
    if len(crossings) != 4:
        raise AssertionError(f"unexpected square crossing count: {len(crossings)}")

    # Preferred polarity: connect crossing points on edges sharing an inside
    # corner. Complementing an ambiguous square therefore selects the other
    # legal connectivity.
    result: List[SegmentKey] = []
    for i, sample_id in enumerate(square):
        if sample_sign(case_index, sample_id):
            previous_edge = edge_key(square[(i - 1) % 4], sample_id)
            next_edge = edge_key(sample_id, square[(i + 1) % 4])
            result.append(segment_key(previous_edge, next_edge))
    return sorted(result)


def lateral_segments(
    case_index: int,
    full_samples: Sequence[int],
    half_samples: Sequence[int],
) -> List[SegmentKey]:
    a, b, c = full_samples
    half_a, half_c = half_samples
    crossings: List[EdgeKey] = []
    if sample_sign(case_index, a) != sample_sign(case_index, b):
        crossings.append(edge_key(a, b))
    if sample_sign(case_index, b) != sample_sign(case_index, c):
        crossings.append(edge_key(b, c))
    if sample_sign(case_index, a) != sample_sign(case_index, c):
        crossings.append(edge_key(half_a, half_c))
    if not crossings:
        return []
    if len(crossings) != 2:
        raise AssertionError(
            f"lateral face should have zero or two crossings, got {crossings}"
        )
    return [segment_key(crossings[0], crossings[1])]


def boundary_segments_by_face(case_index: int) -> Dict[str, List[SegmentKey]]:
    result: Dict[str, List[SegmentKey]] = {}
    for name, square in FULL_QUADRANTS:
        result[name] = square_segments(case_index, square)
    result[HALF_FACE[0]] = square_segments(case_index, HALF_FACE[1])
    for name, full_samples, half_samples in LATERAL_FACES:
        result[name] = lateral_segments(case_index, full_samples, half_samples)
    return result


def flatten_segments(by_face: Dict[str, List[SegmentKey]]) -> List[SegmentKey]:
    return [segment for segments in by_face.values() for segment in segments]


def canonical_cycle(vertices: Sequence[EdgeKey]) -> Tuple[EdgeKey, ...]:
    if not vertices:
        return ()
    seq = tuple(vertices)
    reverse = tuple(reversed(seq))
    candidates = []
    for source in (seq, reverse):
        for i in range(len(source)):
            candidates.append(source[i:] + source[:i])
    return min(candidates)


def trace_boundary_loops(segments: Sequence[SegmentKey]) -> Dict[str, object]:
    adjacency: Dict[EdgeKey, List[Tuple[EdgeKey, int]]] = defaultdict(list)
    for segment_id, (a, b) in enumerate(segments):
        adjacency[a].append((b, segment_id))
        adjacency[b].append((a, segment_id))
    bad_degrees = {
        repr(vertex): len(neighbors)
        for vertex, neighbors in adjacency.items()
        if len(neighbors) != 2
    }
    if bad_degrees:
        return {
            "status": "FAIL_NON_MANIFOLD_BOUNDARY_GRAPH",
            "loops": [],
            "bad_degrees": bad_degrees,
        }

    used = set()
    loops: List[Tuple[EdgeKey, ...]] = []
    for segment_id, segment in enumerate(segments):
        if segment_id in used:
            continue
        start, current = segment
        used.add(segment_id)
        loop = [start]
        while current != start:
            loop.append(current)
            options = [
                (neighbor, edge_id)
                for neighbor, edge_id in adjacency[current]
                if edge_id not in used
            ]
            if not options:
                return {
                    "status": "FAIL_OPEN_BOUNDARY_PATH",
                    "loops": [],
                    "bad_degrees": {},
                }
            neighbor, edge_id = min(options, key=lambda item: (item[0], item[1]))
            used.add(edge_id)
            current = neighbor
        loops.append(canonical_cycle(loop))
    loops.sort()
    return {
        "status": "PASS",
        "loops": loops,
        "bad_degrees": {},
    }


def edge_position(edge: EdgeKey) -> Vec3:
    a, b = edge
    pa = SAMPLE_POSITIONS[a]
    pb = SAMPLE_POSITIONS[b]
    return (
        (pa[0] + pb[0]) * 0.5,
        (pa[1] + pb[1]) * 0.5,
        (pa[2] + pb[2]) * 0.5,
    )


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length2(a: Vec3) -> float:
    return dot(a, a)


def distance2(a: Vec3, b: Vec3) -> float:
    return length2(vsub(a, b))


def triangle_area_squared(triangle: Triangle) -> float:
    a, b, c = (edge_position(vertex) for vertex in triangle)
    return length2(cross(vsub(b, a), vsub(c, a)))


def triangle_score(triangle: Triangle) -> float:
    a, b, c = (edge_position(vertex) for vertex in triangle)
    return distance2(a, b) + distance2(b, c) + distance2(c, a)


def triangulate_loop_dp(loop: Sequence[EdgeKey]) -> Optional[List[Triangle]]:
    count = len(loop)
    if count < 3:
        return None
    dp: List[List[Optional[Tuple[float, List[Triangle]]]]] = [
        [None] * count for _ in range(count)
    ]
    for i in range(count):
        dp[i][i] = (0.0, [])
    for i in range(count - 1):
        dp[i][i + 1] = (0.0, [])

    for span in range(2, count):
        for i in range(count - span):
            j = i + span
            best: Optional[Tuple[float, List[Triangle]]] = None
            for k in range(i + 1, j):
                left = dp[i][k]
                right = dp[k][j]
                triangle = triangle_key(loop[i], loop[k], loop[j])
                if (
                    left is None
                    or right is None
                    or triangle_area_squared(triangle) <= 1.0e-12
                ):
                    continue
                triangles = left[1] + right[1] + [triangle]
                score = left[0] + right[0] + triangle_score(triangle)
                candidate = (score, triangles)
                if best is None or (candidate[0], candidate[1]) < (best[0], best[1]):
                    best = candidate
            dp[i][j] = best
    result = dp[0][count - 1]
    return None if result is None else result[1]


def all_loop_triangulations(
    loop: Sequence[EdgeKey],
    limit: int = 50000,
) -> List[List[Triangle]]:
    count = len(loop)

    @lru_cache(maxsize=None)
    def recurse(i: int, j: int) -> Tuple[Tuple[Triangle, ...], ...]:
        if j <= i + 1:
            return ((),)
        result: List[Tuple[Triangle, ...]] = []
        for k in range(i + 1, j):
            triangle = triangle_key(loop[i], loop[k], loop[j])
            if triangle_area_squared(triangle) <= 1.0e-12:
                continue
            for left in recurse(i, k):
                for right in recurse(k, j):
                    result.append(left + right + (triangle,))
                    if len(result) >= limit:
                        return tuple(result)
        return tuple(result)

    options = [list(option) for option in recurse(0, count - 1)]
    options.sort(key=lambda triangles: (
        sum(triangle_score(triangle) for triangle in triangles),
        triangles,
    ))
    return options


def bbox(triangle: Tuple[Vec3, Vec3, Vec3]) -> Tuple[Vec3, Vec3]:
    return (
        tuple(min(point[i] for point in triangle) for i in range(3)),  # type: ignore[return-value]
        tuple(max(point[i] for point in triangle) for i in range(3)),  # type: ignore[return-value]
    )


def point_in_triangle_3d(
    point: Vec3,
    triangle: Tuple[Vec3, Vec3, Vec3],
    eps: float = 1.0e-9,
) -> bool:
    a, b, c = triangle
    normal = cross(vsub(b, a), vsub(c, a))
    if length2(normal) <= eps:
        return False
    if abs(dot(vsub(point, a), normal)) > 1.0e-7:
        return False
    v0 = vsub(c, a)
    v1 = vsub(b, a)
    v2 = vsub(point, a)
    dot00 = dot(v0, v0)
    dot01 = dot(v0, v1)
    dot02 = dot(v0, v2)
    dot11 = dot(v1, v1)
    dot12 = dot(v1, v2)
    denominator = dot00 * dot11 - dot01 * dot01
    if abs(denominator) <= eps:
        return False
    inv = 1.0 / denominator
    u = (dot11 * dot02 - dot01 * dot12) * inv
    v = (dot00 * dot12 - dot01 * dot02) * inv
    return u >= -eps and v >= -eps and u + v <= 1.0 + eps


def segment_intersects_triangle(
    p0: Vec3,
    p1: Vec3,
    triangle: Tuple[Vec3, Vec3, Vec3],
    eps: float = 1.0e-9,
) -> bool:
    a, b, c = triangle
    normal = cross(vsub(b, a), vsub(c, a))
    if length2(normal) <= eps:
        return False
    d0 = dot(vsub(p0, a), normal)
    d1 = dot(vsub(p1, a), normal)
    if abs(d0) <= eps and abs(d1) <= eps:
        return False
    if d0 * d1 > eps:
        return False
    denominator = d0 - d1
    if abs(denominator) <= eps:
        return False
    t = d0 / denominator
    if t < -eps or t > 1.0 + eps:
        return False
    point = (
        p0[0] + (p1[0] - p0[0]) * t,
        p0[1] + (p1[1] - p0[1]) * t,
        p0[2] + (p1[2] - p0[2]) * t,
    )
    return point_in_triangle_3d(point, triangle, eps)


def project2(point: Vec3, drop_axis: int) -> Vec2:
    if drop_axis == 0:
        return (point[1], point[2])
    if drop_axis == 1:
        return (point[0], point[2])
    return (point[0], point[1])


def orient2(a: Vec2, b: Vec2, c: Vec2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def point_in_triangle_2d(point: Vec2, triangle: Tuple[Vec2, Vec2, Vec2]) -> bool:
    a, b, c = triangle
    values = (orient2(a, b, point), orient2(b, c, point), orient2(c, a, point))
    has_negative = any(value < -1.0e-9 for value in values)
    has_positive = any(value > 1.0e-9 for value in values)
    return not (has_negative and has_positive)


def on_segment2(a: Vec2, b: Vec2, point: Vec2) -> bool:
    return (
        min(a[0], b[0]) - 1.0e-9 <= point[0] <= max(a[0], b[0]) + 1.0e-9
        and min(a[1], b[1]) - 1.0e-9 <= point[1] <= max(a[1], b[1]) + 1.0e-9
        and abs(orient2(a, b, point)) <= 1.0e-9
    )


def segments_intersect2(a: Vec2, b: Vec2, c: Vec2, d: Vec2) -> bool:
    o1 = orient2(a, b, c)
    o2 = orient2(a, b, d)
    o3 = orient2(c, d, a)
    o4 = orient2(c, d, b)
    if o1 * o2 < -1.0e-9 and o3 * o4 < -1.0e-9:
        return True
    return (
        on_segment2(a, b, c)
        or on_segment2(a, b, d)
        or on_segment2(c, d, a)
        or on_segment2(c, d, b)
    )


def coplanar_overlap(
    a: Tuple[Vec3, Vec3, Vec3],
    b: Tuple[Vec3, Vec3, Vec3],
) -> bool:
    normal = cross(vsub(a[1], a[0]), vsub(a[2], a[0]))
    drop_axis = max(range(3), key=lambda axis: abs(normal[axis]))
    pa = tuple(project2(point, drop_axis) for point in a)
    pb = tuple(project2(point, drop_axis) for point in b)
    for i in range(3):
        for j in range(3):
            if segments_intersect2(
                pa[i], pa[(i + 1) % 3], pb[j], pb[(j + 1) % 3]
            ):
                return True
    return point_in_triangle_2d(pa[0], pb) or point_in_triangle_2d(pb[0], pa)


def triangles_intersect_nonadjacent(a: Triangle, b: Triangle) -> bool:
    shared_vertices = set(a) & set(b)
    if shared_vertices:
        return False
    ta = tuple(edge_position(vertex) for vertex in a)
    tb = tuple(edge_position(vertex) for vertex in b)
    amin, amax = bbox(ta)
    bmin, bmax = bbox(tb)
    for axis in range(3):
        if amax[axis] < bmin[axis] - 1.0e-9:
            return False
        if bmax[axis] < amin[axis] - 1.0e-9:
            return False
    na = cross(vsub(ta[1], ta[0]), vsub(ta[2], ta[0]))
    nb = cross(vsub(tb[1], tb[0]), vsub(tb[2], tb[0]))
    if (
        length2(cross(na, nb)) <= 1.0e-12
        and all(abs(dot(vsub(point, ta[0]), na)) <= 1.0e-7 for point in tb)
    ):
        return coplanar_overlap(ta, tb)
    for p0, p1 in ((ta[0], ta[1]), (ta[1], ta[2]), (ta[2], ta[0])):
        if segment_intersects_triangle(p0, p1, tb):
            return True
    for p0, p1 in ((tb[0], tb[1]), (tb[1], tb[2]), (tb[2], tb[0])):
        if segment_intersects_triangle(p0, p1, ta):
            return True
    return False


def intersection_pairs(triangles: Sequence[Triangle]) -> List[Tuple[int, int]]:
    result = []
    for i in range(len(triangles)):
        for j in range(i + 1, len(triangles)):
            if triangles_intersect_nonadjacent(triangles[i], triangles[j]):
                result.append((i, j))
    return result


def polygon_area(points: Sequence[Vec2]) -> float:
    return 0.5 * sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )


def point_in_polygon(point: Vec2, polygon: Sequence[Vec2]) -> bool:
    x, y = point
    inside = False
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        if (a[1] > y) != (b[1] > y):
            crossing_x = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing_x:
                inside = not inside
    return inside


def full_face_nesting(
    loops: Sequence[Sequence[EdgeKey]],
) -> List[Tuple[int, int]]:
    planar: List[Tuple[int, List[Vec2]]] = []
    for loop_id, loop in enumerate(loops):
        positions = [edge_position(vertex) for vertex in loop]
        if all(abs(position[2]) <= 1.0e-9 for position in positions):
            planar.append((loop_id, [(p[0], p[1]) for p in positions]))
    result = []
    for outer_id, outer in planar:
        for inner_id, inner in planar:
            if outer_id != inner_id and point_in_polygon(inner[0], outer):
                result.append((outer_id, inner_id))
    return result


def triangle_edges(triangle: Triangle) -> Tuple[SegmentKey, SegmentKey, SegmentKey]:
    a, b, c = triangle
    return segment_key(a, b), segment_key(b, c), segment_key(c, a)


def validate_triangle_complex(
    triangles: Sequence[Triangle],
    expected_boundary: Sequence[SegmentKey],
) -> Dict[str, object]:
    edge_counts: Counter[SegmentKey] = Counter()
    degenerate = []
    for triangle_id, triangle in enumerate(triangles):
        if len(set(triangle)) != 3 or triangle_area_squared(triangle) <= 1.0e-12:
            degenerate.append(triangle_id)
        edge_counts.update(triangle_edges(triangle))
    actual_boundary = Counter(
        edge for edge, count in edge_counts.items() if count == 1
    )
    expected = Counter(expected_boundary)
    overused_edges = [
        repr(edge) for edge, count in edge_counts.items() if count > 2
    ]
    intersections = intersection_pairs(triangles)
    return {
        "status": (
            "PASS"
            if not degenerate
            and not overused_edges
            and actual_boundary == expected
            and not intersections
            else "FAIL"
        ),
        "degenerate_triangle_ids": degenerate,
        "overused_edges": overused_edges,
        "missing_boundary_segments": [
            repr(edge) for edge, count in (expected - actual_boundary).items()
            for _ in range(count)
        ],
        "extra_boundary_segments": [
            repr(edge) for edge, count in (actual_boundary - expected).items()
            for _ in range(count)
        ],
        "intersection_pairs": [list(pair) for pair in intersections],
    }


def annulus_candidate(
    outer_loop: Sequence[EdgeKey],
    inner_loop: Sequence[EdgeKey],
) -> Optional[List[Triangle]]:
    """Triangulate a planar annulus by enumerating cyclic zipper paths."""
    outer_points = [(edge_position(v)[0], edge_position(v)[1]) for v in outer_loop]
    inner_points = [(edge_position(v)[0], edge_position(v)[1]) for v in inner_loop]
    if abs(polygon_area(outer_points)) < abs(polygon_area(inner_points)):
        outer_loop, inner_loop = inner_loop, outer_loop
        outer_points, inner_points = inner_points, outer_points
    if polygon_area(outer_points) < 0:
        outer_loop = tuple(reversed(outer_loop))
        outer_points = list(reversed(outer_points))

    expected_boundary = [
        segment_key(outer_loop[i], outer_loop[(i + 1) % len(outer_loop)])
        for i in range(len(outer_loop))
    ] + [
        segment_key(inner_loop[i], inner_loop[(i + 1) % len(inner_loop)])
        for i in range(len(inner_loop))
    ]
    target_area = abs(polygon_area(outer_points)) - abs(polygon_area(inner_points))
    best: Optional[Tuple[float, List[Triangle]]] = None

    for outer_direction in (1, -1):
        for inner_direction in (1, -1):
            for outer_start in range(len(outer_loop)):
                ordered_outer = [
                    outer_loop[(outer_start + outer_direction * i) % len(outer_loop)]
                    for i in range(len(outer_loop))
                ]
                for inner_start in range(len(inner_loop)):
                    ordered_inner = [
                        inner_loop[(inner_start + inner_direction * i) % len(inner_loop)]
                        for i in range(len(inner_loop))
                    ]
                    step_count = len(ordered_outer) + len(ordered_inner)
                    for outer_steps in itertools.combinations(
                        range(step_count), len(ordered_outer)
                    ):
                        outer_step_set = set(outer_steps)
                        oi = 0
                        ii = 0
                        triangles: List[Triangle] = []
                        valid = True
                        for step in range(step_count):
                            current_outer = ordered_outer[oi % len(ordered_outer)]
                            current_inner = ordered_inner[ii % len(ordered_inner)]
                            if step in outer_step_set:
                                next_outer = ordered_outer[(oi + 1) % len(ordered_outer)]
                                triangle = triangle_key(
                                    current_outer, next_outer, current_inner
                                )
                                oi += 1
                            else:
                                next_inner = ordered_inner[(ii + 1) % len(ordered_inner)]
                                triangle = triangle_key(
                                    current_outer, next_inner, current_inner
                                )
                                ii += 1
                            if triangle_area_squared(triangle) <= 1.0e-12:
                                valid = False
                                break
                            triangles.append(triangle)
                        if not valid:
                            continue
                        validation = validate_triangle_complex(
                            triangles, expected_boundary
                        )
                        if validation["status"] != "PASS":
                            continue
                        area_sum = 0.0
                        centroids_valid = True
                        for triangle in triangles:
                            points = [edge_position(vertex) for vertex in triangle]
                            area_sum += abs(polygon_area([
                                (point[0], point[1]) for point in points
                            ]))
                            centroid = (
                                sum(point[0] for point in points) / 3.0,
                                sum(point[1] for point in points) / 3.0,
                            )
                            if (
                                not point_in_polygon(centroid, outer_points)
                                or point_in_polygon(centroid, inner_points)
                            ):
                                centroids_valid = False
                                break
                        if not centroids_valid or abs(area_sum - target_area) > 1.0e-8:
                            continue
                        score = sum(triangle_score(triangle) for triangle in triangles)
                        if best is None or (score, triangles) < (best[0], best[1]):
                            best = (score, triangles)
    return None if best is None else best[1]


def select_nonintersecting_loop_fills(
    loops: Sequence[Sequence[EdgeKey]],
) -> Tuple[Optional[List[Triangle]], str]:
    initial: List[Triangle] = []
    for loop in loops:
        triangles = triangulate_loop_dp(loop)
        if triangles is None:
            return None, "failed_dynamic_programming"
        initial.extend(triangles)
    if not intersection_pairs(initial):
        return initial, "shortest_diagonal_dynamic_programming"

    options: List[List[List[Triangle]]] = []
    for loop in loops:
        loop_options = [
            candidate for candidate in all_loop_triangulations(loop)
            if not intersection_pairs(candidate)
        ]
        if not loop_options:
            return None, "no_nonintersecting_loop_triangulation"
        options.append(loop_options)
    order = sorted(range(len(options)), key=lambda index: len(options[index]))

    def search(position: int, selected: List[Triangle]) -> Optional[List[Triangle]]:
        if position == len(order):
            return list(selected)
        loop_id = order[position]
        for candidate in options[loop_id]:
            combined = selected + candidate
            if not intersection_pairs(combined):
                result = search(position + 1, combined)
                if result is not None:
                    return result
        return None

    return search(0, []), "enumerated_nonintersecting_loop_triangulations"


def derive_case_candidate(case_index: int) -> Dict[str, object]:
    by_face = boundary_segments_by_face(case_index)
    segments = flatten_segments(by_face)
    loop_report = trace_boundary_loops(segments)
    if loop_report["status"] != "PASS":
        return {
            "case": case_index,
            "status": "FAIL_BOUNDARY_LOOPS",
            "boundary": loop_report,
            "triangles": [],
        }
    loops: List[Tuple[EdgeKey, ...]] = list(loop_report["loops"])  # type: ignore[arg-type]
    nesting = full_face_nesting(loops)
    used_loops = set()
    triangles: List[Triangle] = []
    methods: List[str] = []

    for outer_id, inner_id in nesting:
        if outer_id in used_loops or inner_id in used_loops:
            continue
        candidate = annulus_candidate(loops[outer_id], loops[inner_id])
        if candidate is None:
            return {
                "case": case_index,
                "status": "FAIL_ANNULUS_TRIANGULATION",
                "boundary": loop_report,
                "triangles": [],
            }
        triangles.extend(candidate)
        used_loops.update((outer_id, inner_id))
        methods.append("planar_annulus_zipper")

    remaining_loops = [
        loop for loop_id, loop in enumerate(loops) if loop_id not in used_loops
    ]
    loop_triangles, method = select_nonintersecting_loop_fills(remaining_loops)
    if loop_triangles is None:
        return {
            "case": case_index,
            "status": "FAIL_LOOP_TRIANGULATION",
            "boundary": loop_report,
            "triangles": [],
            "methods": methods + [method],
        }
    triangles.extend(loop_triangles)
    if remaining_loops:
        methods.append(method)

    validation = validate_triangle_complex(triangles, segments)
    return {
        "case": case_index,
        "status": "PASS" if validation["status"] == "PASS" else "FAIL_VALIDATION",
        "inside_count": case_index.bit_count(),
        "ambiguity": ambiguity_flags(case_index),
        "segments_by_face": by_face,
        "segments": segments,
        "loops": loops,
        "loop_lengths": sorted(len(loop) for loop in loops),
        "nesting": [list(pair) for pair in nesting],
        "methods": methods,
        "triangles": triangles,
        "triangle_count": len(triangles),
        "validation": validation,
    }


def official_anchor_edges() -> Tuple[EdgeKey, ...]:
    anchors = set()
    for _, square in FULL_QUADRANTS:
        for i in range(4):
            a = square[i]
            b = square[(i + 1) % 4]
            ax, ay = GRID_COORDS[a]
            bx, by = GRID_COORDS[b]
            if abs(ax - bx) + abs(ay - by) == 1:
                anchors.add(edge_key(a, b))
    square = HALF_FACE[1]
    for i in range(4):
        anchors.add(edge_key(square[i], square[(i + 1) % 4]))
    return tuple(sorted(anchors))


OFFICIAL_ANCHOR_EDGES = set(official_anchor_edges())


def contract_segments_to_anchor_pairings(
    segments: Sequence[SegmentKey],
) -> Dict[str, object]:
    adjacency: Dict[EdgeKey, List[Tuple[EdgeKey, int]]] = defaultdict(list)
    for segment_id, (a, b) in enumerate(segments):
        adjacency[a].append((b, segment_id))
        adjacency[b].append((a, segment_id))
    used = set()
    pairings: List[SegmentKey] = []
    for anchor in sorted(OFFICIAL_ANCHOR_EDGES & set(adjacency)):
        for neighbor, segment_id in adjacency[anchor]:
            if segment_id in used:
                continue
            used.add(segment_id)
            current = neighbor
            while current not in OFFICIAL_ANCHOR_EDGES:
                options = [
                    (next_vertex, edge_id)
                    for next_vertex, edge_id in adjacency[current]
                    if edge_id not in used
                ]
                if not options:
                    break
                current, edge_id = min(options, key=lambda item: (item[0], item[1]))
                used.add(edge_id)
            if current in OFFICIAL_ANCHOR_EDGES:
                pairings.append(segment_key(anchor, current))
    unused_segment_count = len(segments) - len(used)
    return {
        "pairings": sorted(pairings),
        "unused_segment_count": unused_segment_count,
    }


def independent_case_boundary_segments(case_record: Dict[str, object]) -> List[SegmentKey]:
    vertex_keys = [
        edge_key(int(vertex["samples"][0]), int(vertex["samples"][1]))
        for vertex in case_record["vertices"]  # type: ignore[index]
    ]
    local_edge_counts: Counter[Tuple[int, int]] = Counter()
    for triangle in case_record["triangles"]:  # type: ignore[index]
        a, b, c = (int(value) for value in triangle["vertices"])
        for x, y in ((a, b), (b, c), (c, a)):
            local_edge_counts[(x, y) if x < y else (y, x)] += 1
    return sorted(
        segment_key(vertex_keys[a], vertex_keys[b])
        for (a, b), count in local_edge_counts.items()
        if count == 1
    )


def json_edge(edge: EdgeKey) -> List[int]:
    return [edge[0], edge[1]]


def json_segment(segment: SegmentKey) -> List[List[int]]:
    return [json_edge(segment[0]), json_edge(segment[1])]


def json_triangle(triangle: Triangle) -> List[List[int]]:
    return [json_edge(vertex) for vertex in triangle]


def serialize_case_candidate(record: Dict[str, object]) -> Dict[str, object]:
    result = dict(record)
    if "segments_by_face" in result:
        result["segments_by_face"] = {
            name: [json_segment(segment) for segment in segments]
            for name, segments in result["segments_by_face"].items()  # type: ignore[union-attr]
        }
    if "segments" in result:
        result["segments"] = [
            json_segment(segment) for segment in result["segments"]  # type: ignore[union-attr]
        ]
    if "loops" in result:
        result["loops"] = [
            [json_edge(vertex) for vertex in loop]
            for loop in result["loops"]  # type: ignore[union-attr]
        ]
    if "triangles" in result:
        result["triangles"] = [
            json_triangle(triangle) for triangle in result["triangles"]  # type: ignore[union-attr]
        ]
    return result


def histogram(values: Iterable[int]) -> Dict[str, int]:
    counts = Counter(values)
    return {str(key): counts[key] for key in sorted(counts)}
