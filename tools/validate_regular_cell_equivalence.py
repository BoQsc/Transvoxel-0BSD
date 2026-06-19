#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the clean-room preferred-polarity regular-cell implementation."""
from __future__ import annotations

from collections import Counter, defaultdict
import itertools
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "regular_cell_equivalence_report.json"
MD = ROOT / "validation" / "regular_cell_equivalence_report.md"

sys.path.insert(0, str(ROOT / "tools"))
import generate_regular as regular  # noqa: E402

sys.path.insert(
    0,
    str(ROOT / "research" / "official_topology" / "m3"),
)
import m3_core as topology  # noqa: E402

Vec2 = Tuple[float, float]
Vertex = Tuple[int, int]
DirectedSegment = Tuple[
    Tuple[Vec2, Vec2],
    Tuple[Vec2, Vec2],
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def permutation_parity(permutation: Sequence[int]) -> int:
    inversions = sum(
        permutation[i] > permutation[j]
        for i in range(3)
        for j in range(i + 1, 3)
    )
    return -1 if inversions % 2 else 1


def cube_rotations(
    positions: Dict[int, Tuple[int, int, int]],
) -> List[Tuple[int, ...]]:
    reverse = {position: sample_id for sample_id, position in positions.items()}
    rotations = set()
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1, 1), repeat=3):
            if (
                permutation_parity(permutation)
                * signs[0]
                * signs[1]
                * signs[2]
                != 1
            ):
                continue
            mapping = []
            for sample_id in range(8):
                source = positions[sample_id]
                target = tuple(
                    source[permutation[axis]]
                    if signs[axis] > 0
                    else 1 - source[permutation[axis]]
                    for axis in range(3)
                )
                mapping.append(reverse[target])
            rotations.add(tuple(mapping))
    return sorted(rotations)


def apply_case_permutation(
    case_index: int,
    permutation: Sequence[int],
) -> int:
    return sum(
        1 << permutation[sample_id]
        for sample_id in range(8)
        if case_index & (1 << sample_id)
    )


def ambiguous_case(
    case_index: int,
    faces: Dict[str, Tuple[int, ...]],
) -> bool:
    for square in faces.values():
        bits = [(case_index >> sample_id) & 1 for sample_id in square]
        if (
            bits[0] == bits[2]
            and bits[1] == bits[3]
            and bits[0] != bits[1]
        ):
            return True
    return False


def derive_behavior_classes(
    positions: Dict[int, Tuple[int, int, int]],
    faces: Dict[str, Tuple[int, ...]],
) -> Tuple[List[Set[int]], Dict[str, int]]:
    rotations = cube_rotations(positions)
    combined_seen = set()
    classes: List[Set[int]] = []
    split_count = 0
    base_count = 0
    for case_index in range(256):
        orbit = {
            apply_case_permutation(case_index, rotation)
            for rotation in rotations
        }
        combined = frozenset(
            orbit | {case ^ 0xFF for case in orbit}
        )
        if combined in combined_seen:
            continue
        combined_seen.add(combined)
        representative = min(
            combined,
            key=lambda value: (value.bit_count(), value),
        )
        representative_orbit = {
            apply_case_permutation(representative, rotation)
            for rotation in rotations
        }
        inverse_orbit = {
            case ^ 0xFF for case in representative_orbit
        }
        base_count += 1
        if (
            ambiguous_case(representative, faces)
            and representative_orbit != inverse_orbit
        ):
            classes.append(representative_orbit)
            classes.append(inverse_orbit)
            split_count += 1
        else:
            classes.append(representative_orbit | inverse_orbit)
    metrics = {
        "cube_rotations": len(rotations),
        "base_rotation_inversion_classes": base_count,
        "preferred_polarity_inverse_splits": split_count,
        "behavior_classes": len(classes),
        "covered_cases": sum(len(group) for group in classes),
    }
    return classes, metrics


def triangle_edge_records(case: Dict[str, Any]) -> Tuple[
    List[Vertex],
    List[Tuple[int, int, int]],
    Counter[Tuple[int, int]],
]:
    vertices = [
        tuple(int(value) for value in vertex["samples"])
        for vertex in case["vertices"]
    ]
    triangles = [
        tuple(int(value) for value in triangle["vertices"])
        for triangle in case["triangles"]
    ]
    uses: Counter[Tuple[int, int]] = Counter()
    for triangle in triangles:
        for a, b in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            uses[tuple(sorted((a, b)))] += 1
    return vertices, triangles, uses


def crossing_key(
    edge: Vertex,
    positions: Dict[int, Tuple[float, float, float]],
    axis: int,
) -> Tuple[Vec2, Vec2]:
    keep = [index for index in range(3) if index != axis]
    points = [
        tuple(float(positions[sample_id][index]) for index in keep)
        for sample_id in edge
    ]
    return tuple(sorted(points))  # type: ignore[return-value]


def regular_face_directions(
    case: Dict[str, Any],
    face_samples: Sequence[int],
    positions: Dict[int, Tuple[float, float, float]],
    axis: int,
) -> Counter[DirectedSegment]:
    allowed = set(face_samples)
    vertices, triangles, uses = triangle_edge_records(case)
    result: Counter[DirectedSegment] = Counter()
    for triangle in triangles:
        for a, b in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            if (
                uses[tuple(sorted((a, b)))] == 1
                and set(vertices[a]) <= allowed
                and set(vertices[b]) <= allowed
            ):
                result[(
                    crossing_key(vertices[a], positions, axis),
                    crossing_key(vertices[b], positions, axis),
                )] += 1
    return result


def case_for_face(
    face_samples: Sequence[int],
    positions: Dict[int, Tuple[int, int, int]],
    axis: int,
    shared_pattern: int,
    private_pattern: int,
) -> int:
    keep = [index for index in range(3) if index != axis]
    face_order = sorted(
        face_samples,
        key=lambda sample_id: tuple(
            positions[sample_id][index] for index in keep
        ),
    )
    private_order = sorted(set(range(8)) - set(face_samples))
    result = 0
    for bit, sample_id in enumerate(face_order):
        if shared_pattern & (1 << bit):
            result |= 1 << sample_id
    for bit, sample_id in enumerate(private_order):
        if private_pattern & (1 << bit):
            result |= 1 << sample_id
    return result


def reverse_counter(
    value: Counter[DirectedSegment],
) -> Counter[DirectedSegment]:
    result: Counter[DirectedSegment] = Counter()
    for (a, b), count in value.items():
        result[(b, a)] += count
    return result


def validate_regular_neighbors(
    cases: Sequence[Dict[str, Any]],
    faces: Dict[str, Tuple[int, ...]],
    positions: Dict[int, Tuple[int, int, int]],
) -> Tuple[int, int]:
    comparisons = 0
    failures = 0
    for positive, negative, axis in (
        ("x_max", "x_min", 0),
        ("y_max", "y_min", 1),
        ("z_max", "z_min", 2),
    ):
        for shared in range(16):
            for private_a in range(16):
                case_a = case_for_face(
                    faces[positive],
                    positions,
                    axis,
                    shared,
                    private_a,
                )
                directed_a = regular_face_directions(
                    cases[case_a],
                    faces[positive],
                    positions,
                    axis,
                )
                for private_b in range(16):
                    case_b = case_for_face(
                        faces[negative],
                        positions,
                        axis,
                        shared,
                        private_b,
                    )
                    directed_b = regular_face_directions(
                        cases[case_b],
                        faces[negative],
                        positions,
                        axis,
                    )
                    if directed_a != reverse_counter(directed_b):
                        failures += 1
                    comparisons += 1
    return comparisons, failures


def remap_m4_crossing(
    edge: Vertex,
    positions: Dict[int, Tuple[float, float, float]],
    offset_x: float,
    offset_y: float,
    divisor: float,
) -> Tuple[Vec2, Vec2]:
    points = [
        (
            (positions[sample_id][0] - offset_x) / divisor,
            (positions[sample_id][1] - offset_y) / divisor,
        )
        for sample_id in edge
    ]
    return tuple(sorted(points))  # type: ignore[return-value]


def m4_face_directions(
    case: Dict[str, Any],
    allowed: Set[int],
    positions: Dict[int, Tuple[float, float, float]],
    offset_x: float,
    offset_y: float,
    divisor: float,
) -> Counter[DirectedSegment]:
    vertices, triangles, uses = triangle_edge_records(case)
    result: Counter[DirectedSegment] = Counter()
    for triangle in triangles:
        for a, b in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            if (
                uses[tuple(sorted((a, b)))] == 1
                and set(vertices[a]) <= allowed
                and set(vertices[b]) <= allowed
            ):
                result[(
                    remap_m4_crossing(
                        vertices[a],
                        positions,
                        offset_x,
                        offset_y,
                        divisor,
                    ),
                    remap_m4_crossing(
                        vertices[b],
                        positions,
                        offset_x,
                        offset_y,
                        divisor,
                    ),
                )] += 1
    return result


def regular_face_case_from_sources(
    face_samples: Sequence[int],
    regular_positions: Dict[int, Tuple[int, int, int]],
    source_by_xy: Dict[Tuple[int, int], int],
    m4_case: int,
    private_pattern: int,
) -> int:
    result = 0
    face_set = set(face_samples)
    for sample_id in face_samples:
        x, y, _z = regular_positions[sample_id]
        source = source_by_xy[(x, y)]
        if m4_case & (1 << source):
            result |= 1 << sample_id
    for bit, sample_id in enumerate(sorted(set(range(8)) - face_set)):
        if private_pattern & (1 << bit):
            result |= 1 << sample_id
    return result


def validate_regular_m4_seams(
    regular_cases: Sequence[Dict[str, Any]],
    regular_faces: Dict[str, Tuple[int, ...]],
    regular_positions: Dict[int, Tuple[int, int, int]],
    m4: Dict[str, Any],
) -> Tuple[int, int]:
    m4_positions = {
        int(record["id"]): tuple(float(value) for value in record["position"])
        for record in m4["samples"]
    }
    comparisons = 0
    failures = 0
    quadrants = (
        ({0, 1, 3, 4}, 0, 0),
        ({1, 2, 4, 5}, 1, 0),
        ({3, 4, 6, 7}, 0, 1),
        ({4, 5, 7, 8}, 1, 1),
    )
    for case_index, m4_case in enumerate(m4["cases"]):
        for allowed, offset_x, offset_y in quadrants:
            m4_directed = m4_face_directions(
                m4_case,
                allowed,
                m4_positions,
                float(offset_x),
                float(offset_y),
                1.0,
            )
            sources = {
                (x, y): (offset_x + x) + 3 * (offset_y + y)
                for x in range(2)
                for y in range(2)
            }
            for private in range(16):
                regular_case = regular_face_case_from_sources(
                    regular_faces["z_max"],
                    regular_positions,
                    sources,
                    case_index,
                    private,
                )
                regular_directed = regular_face_directions(
                    regular_cases[regular_case],
                    regular_faces["z_max"],
                    regular_positions,
                    2,
                )
                if m4_directed != reverse_counter(regular_directed):
                    failures += 1
                comparisons += 1

        m4_directed = m4_face_directions(
            m4_case,
            {9, 10, 11, 12},
            m4_positions,
            0.0,
            0.0,
            2.0,
        )
        sources = {
            (0, 0): 0,
            (1, 0): 2,
            (0, 1): 6,
            (1, 1): 8,
        }
        for private in range(16):
            regular_case = regular_face_case_from_sources(
                regular_faces["z_min"],
                regular_positions,
                sources,
                case_index,
                private,
            )
            regular_directed = regular_face_directions(
                regular_cases[regular_case],
                regular_faces["z_min"],
                regular_positions,
                2,
            )
            if m4_directed != reverse_counter(regular_directed):
                failures += 1
            comparisons += 1
    return comparisons, failures


def topology_and_winding_metrics(
    table: Dict[str, Any],
    positions: Dict[int, Tuple[int, int, int]],
) -> Tuple[Dict[str, int], List[str]]:
    metrics = {
        "cases": 0,
        "vertices": 0,
        "triangles": 0,
        "max_vertices": 0,
        "max_triangles": 0,
        "boundary_failures": 0,
        "intersection_failures": 0,
        "topology_failures": 0,
        "winding_failures": 0,
        "inactive_edge_vertices": 0,
    }
    failures: List[str] = []
    old_positions = topology.SAMPLE_POSITIONS
    topology.SAMPLE_POSITIONS = {
        sample_id: tuple(float(value) for value in position)
        for sample_id, position in positions.items()
    }
    try:
        for case in table["cases"]:
            case_index = int(case["case"])
            vertices = [
                tuple(int(value) for value in vertex["samples"])
                for vertex in case["vertices"]
            ]
            triangles = [
                tuple(vertices[int(index)] for index in triangle["vertices"])
                for triangle in case["triangles"]
            ]
            expected_boundary = [
                topology.segment_key(
                    tuple(int(value) for value in segment[0]),
                    tuple(int(value) for value in segment[1]),
                )
                for segment in case["boundary_segments"]
            ]
            validation = topology.validate_triangle_complex(
                triangles,
                expected_boundary,
            )
            if validation["status"] != "PASS":
                metrics["topology_failures"] += 1
                failures.append(f"case {case_index}: invalid triangle complex")
            if validation["missing_boundary_segments"] or validation[
                "extra_boundary_segments"
            ]:
                metrics["boundary_failures"] += 1
            if validation["intersection_pairs"]:
                metrics["intersection_failures"] += 1
            for a, b in vertices:
                if (
                    regular.sign_for_sample(case_index, a)
                    == regular.sign_for_sample(case_index, b)
                ):
                    metrics["inactive_edge_vertices"] += 1

            uses: Dict[
                Tuple[Vertex, Vertex],
                List[Tuple[int, Vertex, Vertex]],
            ] = defaultdict(list)
            for triangle_id, triangle in enumerate(triangles):
                for a, b in (
                    (triangle[0], triangle[1]),
                    (triangle[1], triangle[2]),
                    (triangle[2], triangle[0]),
                ):
                    uses[topology.segment_key(a, b)].append(
                        (triangle_id, a, b)
                    )
            adjacency: Dict[int, Set[int]] = defaultdict(set)
            coherent = True
            for edge_uses in uses.values():
                if len(edge_uses) == 2:
                    first, second = edge_uses
                    if first[1:] == second[1:]:
                        coherent = False
                    adjacency[first[0]].add(second[0])
                    adjacency[second[0]].add(first[0])
            seen = set()
            outward = coherent
            for start in range(len(triangles)):
                if start in seen:
                    continue
                seen.add(start)
                pending = [start]
                component = []
                while pending:
                    triangle_id = pending.pop()
                    component.append(triangle_id)
                    for neighbor in adjacency[triangle_id]:
                        if neighbor not in seen:
                            seen.add(neighbor)
                            pending.append(neighbor)
                score = 0.0
                for triangle_id in component:
                    points = [
                        regular.edge_midpoint(vertex)
                        for vertex in triangles[triangle_id]
                    ]
                    normal = regular.cross(
                        regular.sub(points[1], points[0]),
                        regular.sub(points[2], points[0]),
                    )
                    centroid = (
                        sum(point[0] for point in points) / 3.0,
                        sum(point[1] for point in points) / 3.0,
                        sum(point[2] for point in points) / 3.0,
                    )
                    score += regular.dot(
                        normal,
                        regular.regular_gradient(case_index, centroid),
                    )
                if score <= 1.0e-12:
                    outward = False
            if not outward:
                metrics["winding_failures"] += 1
                failures.append(f"case {case_index}: winding failure")
            metrics["cases"] += 1
            metrics["vertices"] += len(vertices)
            metrics["triangles"] += len(triangles)
            metrics["max_vertices"] = max(
                metrics["max_vertices"],
                len(vertices),
            )
            metrics["max_triangles"] = max(
                metrics["max_triangles"],
                len(triangles),
            )
    finally:
        topology.SAMPLE_POSITIONS = old_positions
    return metrics, failures


def write_markdown(report: Dict[str, Any]) -> None:
    metrics = report["metrics"]
    lines = [
        "# Clean-Room Regular-Cell Equivalence",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Functional regular-cell behavior: **{report['functional_regular_cell_equivalence']}**",
        "",
        "## Exhaustive coverage",
        "",
        f"- Cases: `{metrics['topology']['cases']}`",
        f"- Behavior classes: `{metrics['classes']['behavior_classes']}`",
        f"- Vertices / triangles: `{metrics['topology']['vertices']}` / `{metrics['topology']['triangles']}`",
        f"- Maximum vertices / triangles: `{metrics['topology']['max_vertices']}` / `{metrics['topology']['max_triangles']}`",
        f"- Regular/regular seam comparisons: `{metrics['regular_neighbor_comparisons']}`",
        f"- Regular/M4 seam comparisons: `{metrics['regular_m4_comparisons']}`",
        f"- Failures: `{len(report['failures'])}`",
        "",
        "This proves clean-room modified-Marching-Cubes behavior and compatibility with the M4 transition boundary. It does not claim official class numbers, vertex reuse codes, or table bytes.",
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    table = read_json(ROOT / "generated" / "regular_tables.json")
    m4 = read_json(
        ROOT / "generated" / "official_topology_candidate_tables.json"
    )
    positions = {
        int(record["id"]): tuple(int(value) for value in record["position"])
        for record in table["sample_positions"]
    }
    faces = {
        str(record["name"]): tuple(int(value) for value in record["samples"])
        for record in table["faces"]
    }
    classes, class_metrics = derive_behavior_classes(positions, faces)
    class_signature_failures = 0
    for group in classes:
        signatures = {
            (
                tuple(sorted(
                    len(loop)
                    for loop in table["cases"][case_index][
                        "boundary_loops"
                    ]
                )),
                len(table["cases"][case_index]["triangles"]),
            )
            for case_index in group
        }
        if len(signatures) != 1:
            class_signature_failures += 1

    topology_metrics, failures = topology_and_winding_metrics(
        table,
        positions,
    )
    neighbor_comparisons, neighbor_failures = validate_regular_neighbors(
        table["cases"],
        faces,
        positions,
    )
    m4_comparisons, m4_failures = validate_regular_m4_seams(
        table["cases"],
        faces,
        positions,
        m4,
    )
    if neighbor_failures:
        failures.append(
            f"regular neighbor seam failures: {neighbor_failures}"
        )
    if m4_failures:
        failures.append(f"regular/M4 seam failures: {m4_failures}")

    checks = {
        "published_corner_numbering_and_case_bits_match": (
            positions == regular.SAMPLE_POSITIONS
            and table["case_bits"]
            == {str(sample_id): 1 << sample_id for sample_id in range(8)}
        ),
        "all_256_cases_are_present": len(table["cases"]) == 256,
        "trivial_cases_are_empty": (
            not table["cases"][0]["triangles"]
            and not table["cases"][255]["triangles"]
        ),
        "modified_marching_cubes_18_behavior_classes": (
            class_metrics == {
                "cube_rotations": 24,
                "base_rotation_inversion_classes": 15,
                "preferred_polarity_inverse_splits": 3,
                "behavior_classes": 18,
                "covered_cases": 256,
            }
            and class_signature_failures == 0
        ),
        "published_vertex_and_triangle_limits_match": (
            topology_metrics["max_vertices"] == 12
            and topology_metrics["max_triangles"] == 5
        ),
        "all_vertices_are_on_active_cube_edges": (
            topology_metrics["inactive_edge_vertices"] == 0
        ),
        "all_triangle_complexes_are_valid_and_outward": (
            topology_metrics["topology_failures"] == 0
            and topology_metrics["boundary_failures"] == 0
            and topology_metrics["intersection_failures"] == 0
            and topology_metrics["winding_failures"] == 0
        ),
        "all_regular_neighbors_match_with_opposite_boundary_winding": (
            neighbor_comparisons == 12288 and neighbor_failures == 0
        ),
        "all_regular_m4_boundaries_match_with_opposite_winding": (
            m4_comparisons == 40960 and m4_failures == 0
        ),
        "derived_total_triangle_count_is_820": (
            topology_metrics["triangles"] == 820
        ),
    }
    ok = all(checks.values()) and not failures
    report = {
        "schema": "boqsc.transvoxel.regular_cell_equivalence.v1",
        "status": (
            "PASS_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE"
            if ok
            else "FAIL_REGULAR_CELL_EQUIVALENCE"
        ),
        "functional_regular_cell_equivalence": (
            "PROVEN" if ok else "NOT_PROVEN"
        ),
        "checks": checks,
        "metrics": {
            "classes": class_metrics,
            "class_signature_failures": class_signature_failures,
            "topology": topology_metrics,
            "regular_neighbor_comparisons": neighbor_comparisons,
            "regular_neighbor_failures": neighbor_failures,
            "regular_m4_comparisons": m4_comparisons,
            "regular_m4_failures": m4_failures,
        },
        "failures": failures[:100],
        "source_reference": {
            "title": "Voxel-Based Terrain for Real-Time Virtual Simulations",
            "author": "Eric Lengyel",
            "url": "https://transvoxel.org/Lengyel-VoxelTerrain.pdf",
            "relevant_public_rules": [
                "Section 3.1.2 and Figure 3.5: preferred-polarity face contours",
                "Section 3.1.2: 15 base classes plus 3 ambiguity inverse splits",
                "Figure 3.8 and Listing 3.1: corner numbering and 8-bit case index",
                "Section 3.2: vertices only on active edges",
                "Section 3.2: at most 12 vertices and 5 triangles",
            ],
        },
        "claim_boundary": {
            "proven": (
                "Functional clean-room modified-Marching-Cubes regular-cell "
                "behavior and crack-free compatibility with M4 transition "
                "boundaries."
            ),
            "not_proven": [
                "official numeric regular class IDs",
                "official vertex reuse/cache codes",
                "Transvoxel.cpp regular table bytes",
            ],
        },
        "no_copy_rule": (
            "Derived from public prose/figures and first principles; no "
            "official regular lookup-table arrays are read or compared."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("regular cell equivalence:", report["status"])
    print(
        "cases=256 classes=",
        class_metrics["behavior_classes"],
        "triangles=",
        topology_metrics["triangles"],
        "regular_seams=",
        neighbor_comparisons,
        "m4_seams=",
        m4_comparisons,
        "failures=",
        len(failures),
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
