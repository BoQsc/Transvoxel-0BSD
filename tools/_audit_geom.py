# SPDX-License-Identifier: 0BSD
"""Small geometry helpers for strict audit scripts. No third-party dependencies."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]
EPS = 1.0e-9


def load_table(root: Path, name: str) -> Dict[str, object]:
    return json.loads((root / "generated" / name).read_text(encoding="utf-8"))


def sample_positions(table: Dict[str, object]) -> Dict[int, Vec3]:
    out: Dict[int, Vec3] = {}
    for item in table["sample_positions"]:  # type: ignore[index]
        out[int(item["id"])] = tuple(float(x) for x in item["position"])  # type: ignore[index]
    return out


def vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


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


def normalize_key(p: Vec3, digits: int = 9) -> Vec3:
    return (round(p[0], digits), round(p[1], digits), round(p[2], digits))


def triangle_normal(tri: Tri) -> Vec3:
    a, b, c = tri
    return cross(vsub(b, a), vsub(c, a))


def triangle_area2(tri: Tri) -> float:
    return math.sqrt(length2(triangle_normal(tri)))


def case_vertices(table: Dict[str, object], case: Dict[str, object]) -> List[Vec3]:
    spos = sample_positions(table)
    out: List[Vec3] = []
    for v in case.get("vertices", []):  # type: ignore[union-attr]
        a, b = v["samples"]  # type: ignore[index]
        pa = spos[int(a)]
        pb = spos[int(b)]
        out.append(vmul(vadd(pa, pb), 0.5))
    return out


def case_triangles(table: Dict[str, object], case: Dict[str, object]) -> List[Tri]:
    verts = case_vertices(table, case)
    out: List[Tri] = []
    for tri in case.get("triangles", []):  # type: ignore[union-attr]
        ids = tri["vertices"]  # type: ignore[index]
        out.append((verts[int(ids[0])], verts[int(ids[1])], verts[int(ids[2])]))
    return out


def tri_unordered_key(tri: Tri) -> Tuple[Vec3, Vec3, Vec3]:
    return tuple(sorted(normalize_key(p) for p in tri))  # type: ignore[return-value]


def bbox(tri: Tri) -> Tuple[Vec3, Vec3]:
    return (
        (min(p[0] for p in tri), min(p[1] for p in tri), min(p[2] for p in tri)),
        (max(p[0] for p in tri), max(p[1] for p in tri), max(p[2] for p in tri)),
    )


def bbox_overlap(a: Tri, b: Tri, eps: float = EPS) -> bool:
    amin, amax = bbox(a)
    bmin, bmax = bbox(b)
    for i in range(3):
        if amax[i] < bmin[i] - eps or bmax[i] < amin[i] - eps:
            return False
    return True


def share_vertex(a: Tri, b: Tri) -> bool:
    aset = {normalize_key(p) for p in a}
    bset = {normalize_key(p) for p in b}
    return bool(aset & bset)


def point_in_tri(p: Vec3, tri: Tri, eps: float = EPS) -> bool:
    a, b, c = tri
    n = triangle_normal(tri)
    n2 = length2(n)
    if n2 <= eps:
        return False
    if abs(dot(vsub(p, a), n)) > 1.0e-7:
        return False
    v0 = vsub(c, a)
    v1 = vsub(b, a)
    v2 = vsub(p, a)
    dot00 = dot(v0, v0)
    dot01 = dot(v0, v1)
    dot02 = dot(v0, v2)
    dot11 = dot(v1, v1)
    dot12 = dot(v1, v2)
    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) <= eps:
        return False
    inv = 1.0 / denom
    u = (dot11 * dot02 - dot01 * dot12) * inv
    v = (dot00 * dot12 - dot01 * dot02) * inv
    return u >= -eps and v >= -eps and (u + v) <= 1.0 + eps


def segment_intersects_tri(p0: Vec3, p1: Vec3, tri: Tri, eps: float = EPS) -> bool:
    a, b, c = tri
    n = triangle_normal(tri)
    n2 = length2(n)
    if n2 <= eps:
        return False
    d0 = dot(vsub(p0, a), n)
    d1 = dot(vsub(p1, a), n)
    if abs(d0) <= eps and abs(d1) <= eps:
        return False  # coplanar handled separately
    if d0 * d1 > eps:
        return False
    denom = d0 - d1
    if abs(denom) <= eps:
        return False
    t = d0 / denom
    if t < -eps or t > 1.0 + eps:
        return False
    p = vadd(p0, vmul(vsub(p1, p0), t))
    return point_in_tri(p, tri, eps)


def project2(p: Vec3, drop_axis: int) -> Tuple[float, float]:
    if drop_axis == 0:
        return (p[1], p[2])
    if drop_axis == 1:
        return (p[0], p[2])
    return (p[0], p[1])


def orient2(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_seg2(a: Tuple[float, float], b: Tuple[float, float], p: Tuple[float, float], eps: float = EPS) -> bool:
    return (
        min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps and
        min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps and
        abs(orient2(a, b, p)) <= eps
    )


def seg_intersect2(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float], d: Tuple[float, float]) -> bool:
    o1 = orient2(a, b, c)
    o2 = orient2(a, b, d)
    o3 = orient2(c, d, a)
    o4 = orient2(c, d, b)
    if o1 * o2 < -EPS and o3 * o4 < -EPS:
        return True
    if on_seg2(a, b, c) or on_seg2(a, b, d) or on_seg2(c, d, a) or on_seg2(c, d, b):
        return True
    return False


def point_in_tri2(p: Tuple[float, float], tri: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]) -> bool:
    a, b, c = tri
    o1 = orient2(a, b, p)
    o2 = orient2(b, c, p)
    o3 = orient2(c, a, p)
    has_neg = o1 < -EPS or o2 < -EPS or o3 < -EPS
    has_pos = o1 > EPS or o2 > EPS or o3 > EPS
    return not (has_neg and has_pos)


def coplanar_overlap(a: Tri, b: Tri) -> bool:
    n = triangle_normal(a)
    ax = max(range(3), key=lambda i: abs(n[i]))
    a2 = tuple(project2(p, ax) for p in a)
    b2 = tuple(project2(p, ax) for p in b)
    edges_a = [(a2[0], a2[1]), (a2[1], a2[2]), (a2[2], a2[0])]
    edges_b = [(b2[0], b2[1]), (b2[1], b2[2]), (b2[2], b2[0])]
    for e1 in edges_a:
        for e2 in edges_b:
            if seg_intersect2(e1[0], e1[1], e2[0], e2[1]):
                return True
    return point_in_tri2(a2[0], b2) or point_in_tri2(b2[0], a2)


def triangles_intersect_nonadjacent(a: Tri, b: Tri) -> bool:
    if not bbox_overlap(a, b):
        return False
    if share_vertex(a, b):
        return False
    na = triangle_normal(a)
    nb = triangle_normal(b)
    # coplanar test
    if length2(cross(na, nb)) <= 1.0e-12 and all(abs(dot(vsub(p, a[0]), na)) <= 1.0e-7 for p in b):
        return coplanar_overlap(a, b)
    for p0, p1 in [(a[0], a[1]), (a[1], a[2]), (a[2], a[0])]:
        if segment_intersects_tri(p0, p1, b):
            return True
    for p0, p1 in [(b[0], b[1]), (b[1], b[2]), (b[2], b[0])]:
        if segment_intersects_tri(p0, p1, a):
            return True
    return False
