#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build a research-only Transvoxel.cpp-compatible data surface.

The generated file preserves the original public data shapes and symbol names,
but assigns its own internal class IDs. Packed reuse codes are generated from
cell geometry formulas. Topology comes from the research-only M24 candidate.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[3]
M25_DIR = ROOT / "research" / "official_topology" / "m25"
GENERATED_DIR = M25_DIR / "generated"
M24_TABLES = (
    ROOT
    / "research"
    / "official_topology"
    / "m24"
    / "generated"
    / "m24_exact_topology_tables.json"
)
CPP_PATH = GENERATED_DIR / "Transvoxel.cpp"
LAYOUT_PATH = GENERATED_DIR / "m25_compatible_layout.json"
REPORT_PATH = ROOT / "validation" / "m25_compatible_layout_report.json"
REPORT_MD_PATH = ROOT / "validation" / "m25_compatible_layout_report.md"

sys.path.insert(0, str(ROOT / "tools"))
import compare_official_oracle as oracle_compare  # noqa: E402

Edge = Tuple[int, int]
Triangle = Tuple[Edge, Edge, Edge]
IndexTriangle = Tuple[int, int, int]

REGULAR_POSITIONS = {
    0: (0, 0, 0),
    1: (1, 0, 0),
    2: (0, 1, 0),
    3: (1, 1, 0),
    4: (0, 0, 1),
    5: (1, 0, 1),
    6: (0, 1, 1),
    7: (1, 1, 1),
}
TRANSITION_POSITIONS = {
    **{i: (i % 3, i // 3, 0) for i in range(9)},
    9: (0, 0, 1),
    10: (2, 0, 1),
    11: (0, 2, 1),
    12: (2, 2, 1),
}


def canonical_triangle(triangle: Triangle) -> Triangle:
    a, b, c = triangle
    return min((a, b, c), (b, c, a), (c, a, b))


def canonical_index_triangle(triangle: IndexTriangle) -> IndexTriangle:
    a, b, c = triangle
    return min((a, b, c), (b, c, a), (c, a, b))


def reversed_triangles(triangles: Sequence[Triangle]) -> List[Triangle]:
    return [(a, c, b) for a, b, c in triangles]


def triangle_info(
    triangles: Sequence[Triangle],
) -> Tuple[
    List[Edge],
    Set[Triangle],
    Counter[Tuple[Edge, Edge]],
    Counter[frozenset[Edge]],
    Dict[Edge, Tuple[int, int, Tuple[int, ...]]],
]:
    vertices = sorted({vertex for triangle in triangles for vertex in triangle})
    triangle_set = {canonical_triangle(triangle) for triangle in triangles}
    directed: Counter[Tuple[Edge, Edge]] = Counter()
    undirected: Counter[frozenset[Edge]] = Counter()
    incidence: Counter[Edge] = Counter()
    for a, b, c in triangle_set:
        for vertex in (a, b, c):
            incidence[vertex] += 1
        for x, y in ((a, b), (b, c), (c, a)):
            directed[(x, y)] += 1
            undirected[frozenset((x, y))] += 1
    invariants = {}
    for vertex in vertices:
        edge_counts = sorted(
            undirected[frozenset((vertex, other))]
            for other in vertices
            if undirected[frozenset((vertex, other))]
        )
        invariants[vertex] = (
            incidence[vertex],
            len(edge_counts),
            tuple(edge_counts),
        )
    return vertices, triangle_set, directed, undirected, invariants


def find_isomorphism(
    source: Sequence[Triangle],
    target: Sequence[Triangle],
) -> Optional[Dict[Edge, Edge]]:
    (
        source_vertices,
        source_triangles,
        source_directed,
        source_undirected,
        source_invariants,
    ) = triangle_info(source)
    (
        target_vertices,
        target_triangles,
        target_directed,
        target_undirected,
        target_invariants,
    ) = triangle_info(target)
    if (
        len(source_vertices) != len(target_vertices)
        or len(source_triangles) != len(target_triangles)
    ):
        return None
    candidates = {
        source_vertex: [
            target_vertex
            for target_vertex in target_vertices
            if source_invariants[source_vertex]
            == target_invariants[target_vertex]
        ]
        for source_vertex in source_vertices
    }
    if any(not values for values in candidates.values()):
        return None
    order = sorted(
        source_vertices,
        key=lambda vertex: (
            len(candidates[vertex]),
            -source_invariants[vertex][0],
            vertex,
        ),
    )
    mapping: Dict[Edge, Edge] = {}
    used: Set[Edge] = set()

    def compatible(source_vertex: Edge, target_vertex: Edge) -> bool:
        for other_source, other_target in mapping.items():
            if (
                source_directed[(source_vertex, other_source)]
                != target_directed[(target_vertex, other_target)]
                or source_directed[(other_source, source_vertex)]
                != target_directed[(other_target, target_vertex)]
                or source_undirected[
                    frozenset((source_vertex, other_source))
                ]
                != target_undirected[
                    frozenset((target_vertex, other_target))
                ]
            ):
                return False
        return True

    def search(position: int) -> Optional[Dict[Edge, Edge]]:
        if position == len(order):
            mapped = {
                canonical_triangle(tuple(mapping[vertex] for vertex in triangle))
                for triangle in source_triangles
            }
            return dict(mapping) if mapped == target_triangles else None
        source_vertex = order[position]
        for target_vertex in candidates[source_vertex]:
            if (
                target_vertex in used
                or not compatible(source_vertex, target_vertex)
            ):
                continue
            mapping[source_vertex] = target_vertex
            used.add(target_vertex)
            result = search(position + 1)
            if result is not None:
                return result
            used.remove(target_vertex)
            del mapping[source_vertex]
        return None

    return search(0)


def case_triangles(
    tables: Dict[str, object],
    section_name: str,
    case_index: int,
) -> List[Triangle]:
    vertices, triangles = oracle_compare.case_from_export(
        tables[section_name],  # type: ignore[arg-type]
        case_index,
    )
    return oracle_compare.edge_triangles(vertices, triangles)


def classify_cases(
    tables: Dict[str, object],
    section_name: str,
    case_count: int,
    allow_reverse: bool,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    classes: List[Dict[str, object]] = []
    assignments: List[Dict[str, object]] = []
    for case_index in range(case_count):
        triangles = case_triangles(tables, section_name, case_index)
        reverse = reversed_triangles(triangles)
        selected: Optional[Tuple[int, Dict[Edge, Edge], bool]] = None
        for class_id, class_record in enumerate(classes):
            representative = class_record["triangles"]  # type: ignore[index]
            mapping = find_isomorphism(representative, triangles)
            if mapping is not None:
                selected = (class_id, mapping, False)
                break
            if allow_reverse:
                mapping = find_isomorphism(representative, reverse)
                if mapping is not None:
                    selected = (class_id, mapping, True)
                    break
        if selected is None:
            vertices = sorted({
                vertex for triangle in triangles for vertex in triangle
            })
            vertex_map = {
                vertex: index for index, vertex in enumerate(vertices)
            }
            indexed = sorted(
                canonical_index_triangle(tuple(
                    vertex_map[vertex] for vertex in triangle
                ))
                for triangle in triangles
            )
            class_id = len(classes)
            classes.append({
                "class_id": class_id,
                "representative_case": case_index,
                "vertices": vertices,
                "triangles": triangles,
                "indexed_triangles": indexed,
            })
            mapping = {vertex: vertex for vertex in vertices}
            selected = (class_id, mapping, False)
        class_id, mapping, flip = selected
        class_record = classes[class_id]
        representative_vertices = class_record["vertices"]  # type: ignore[index]
        ordered_vertices = [
            mapping[vertex] for vertex in representative_vertices
        ]
        assignments.append({
            "case": case_index,
            "class_id": class_id,
            "flip": flip,
            "vertices": ordered_vertices,
        })
    return classes, assignments


def regular_vertex_code(edge: Edge) -> int:
    a, b = edge
    pa = REGULAR_POSITIONS[a]
    pb = REGULAR_POSITIONS[b]
    differing = [axis for axis in range(3) if pa[axis] != pb[axis]]
    if len(differing) != 1:
        raise ValueError(f"not a regular cube edge: {edge}")
    axis = differing[0]
    other_axes = [value for value in range(3) if value != axis]
    fixed = [pa[value] for value in other_axes]
    direction_bits = (1, 2, 4)
    if all(value == 1 for value in fixed):
        reuse_direction = 8
    else:
        reuse_direction = sum(
            direction_bits[other_axis]
            for other_axis in other_axes
            if pa[other_axis] == 0
        )
    reuse_index = (2, 1, 3)[axis]
    low = (a << 4) | b
    high = (reuse_direction << 4) | reuse_index
    return (high << 8) | low


def transition_vertex_code(edge: Edge) -> int:
    a, b = edge
    pa = TRANSITION_POSITIONS[a]
    pb = TRANSITION_POSITIONS[b]
    if pa[2] != pb[2]:
        raise ValueError(f"transition edge crosses layers: {edge}")
    horizontal = pa[1] == pb[1]
    vertical = pa[0] == pb[0]
    if horizontal == vertical:
        raise ValueError(f"not a transition grid edge: {edge}")
    half_resolution = pa[2] == 1
    if horizontal:
        coordinate = pa[1]
        if coordinate == 0:
            reuse_direction = 2
        elif coordinate == 2:
            reuse_direction = 8
        else:
            reuse_direction = 4
        if half_resolution:
            reuse_index = 8
        else:
            reuse_index = 3 if min(pa[0], pb[0]) == 0 else 4
    else:
        coordinate = pa[0]
        if coordinate == 0:
            reuse_direction = 1
        elif coordinate == 2:
            reuse_direction = 8
        else:
            reuse_direction = 4
        if half_resolution:
            reuse_index = 9
        else:
            reuse_index = 5 if min(pa[1], pb[1]) == 0 else 6
    low = (a << 4) | b
    high = (reuse_direction << 4) | reuse_index
    return (high << 8) | low


def transition_corner_code(sample_id: int) -> int:
    x, y, layer = TRANSITION_POSITIONS[sample_id]
    if y == 0:
        reuse_direction = 2 + (1 if x == 0 else 0)
    elif x == 0:
        reuse_direction = 1
    elif x == 2 or y == 2:
        reuse_direction = 8
    else:
        reuse_direction = 4
    if layer == 1:
        reuse_index = 7
    elif x == 1 and y in (0, 2):
        reuse_index = 1
    elif y == 1 and x in (0, 2):
        reuse_index = 2
    else:
        reuse_index = 0
    return (reuse_direction << 4) | reuse_index


def class_data(
    classes: Sequence[Dict[str, object]],
    capacity: int,
) -> List[Dict[str, object]]:
    result = []
    for record in classes:
        indexed = record["indexed_triangles"]  # type: ignore[index]
        vertices = record["vertices"]  # type: ignore[index]
        result.append({
            "vertex_count": len(vertices),
            "triangle_count": len(indexed),
            "indices": [
                value for triangle in indexed for value in triangle
            ],
        })
    while len(result) < capacity:
        result.append({
            "vertex_count": 0,
            "triangle_count": 0,
            "indices": [],
        })
    if len(result) != capacity:
        raise ValueError(
            f"class capacity {capacity} too small for {len(classes)} classes"
        )
    return result


def inverse_transition_case_map() -> List[int]:
    result = [-1] * 512
    for local_case in range(512):
        official_case = (
            oracle_compare.local_transition_to_official_case(local_case)
        )
        result[official_case] = local_case
    if any(value < 0 for value in result):
        raise ValueError("transition case mapping is not bijective")
    return result


def build_layout() -> Dict[str, object]:
    tables = json.loads(M24_TABLES.read_text(encoding="utf-8"))
    regular_classes, regular_assignments = classify_cases(
        tables,
        "regular",
        256,
        False,
    )
    transition_classes, transition_assignments = classify_cases(
        tables,
        "transition",
        512,
        True,
    )
    if len(regular_classes) > 16 or len(transition_classes) > 56:
        raise ValueError(
            "compatible class capacities exceeded: "
            f"{len(regular_classes)} / {len(transition_classes)}"
        )

    regular_case_class = [
        int(record["class_id"]) for record in regular_assignments
    ]
    regular_vertices = [
        [regular_vertex_code(edge) for edge in record["vertices"]]
        for record in regular_assignments
    ]

    inverse_cases = inverse_transition_case_map()
    transition_case_class = [0] * 512
    transition_vertices: List[List[int]] = [[] for _ in range(512)]
    for official_case, local_case in enumerate(inverse_cases):
        assignment = transition_assignments[local_case]
        code = int(assignment["class_id"])
        if assignment["flip"]:
            code |= 0x80
        transition_case_class[official_case] = code
        transition_vertices[official_case] = [
            transition_vertex_code(edge)
            for edge in assignment["vertices"]
        ]

    layout: Dict[str, object] = {
        "schema": "boqsc.transvoxel.m25.compatible_layout.v1",
        "status": "M25_RESEARCH_ONLY_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT",
        "generator_code_license": "0BSD",
        "generated_data_license_status": (
            "RESEARCH_ONLY_NOT_YET_CLEARED_FOR_0BSD_RELEASE"
        ),
        "meaning": (
            "Original data ABI shapes and symbol semantics with independent "
            "internal class numbering, formula-derived reuse codes, and M24 "
            "exact topology."
        ),
        "source": {
            "m24_tables": (
                "research/official_topology/m24/generated/"
                "m24_exact_topology_tables.json"
            ),
            "m24_sha256": hashlib.sha256(
                M24_TABLES.read_bytes()
            ).hexdigest(),
        },
        "regular": {
            "case_count": 256,
            "class_capacity": 16,
            "used_class_count": len(regular_classes),
            "case_class": regular_case_class,
            "class_data": class_data(regular_classes, 16),
            "vertex_data": regular_vertices,
        },
        "transition": {
            "case_count": 512,
            "class_capacity": 56,
            "used_class_count": len(transition_classes),
            "case_class": transition_case_class,
            "class_data": class_data(transition_classes, 56),
            "corner_data": [
                transition_corner_code(sample_id)
                for sample_id in range(13)
            ],
            "vertex_data": transition_vertices,
            "official_case_to_local_case": inverse_cases,
        },
        "compatibility_boundary": {
            "same_struct_names": True,
            "same_symbol_names": True,
            "same_array_capacities": True,
            "same_packed_code_semantics": True,
            "same_internal_numeric_class_ids": False,
            "byte_identity": False,
            "unchanged_consumer_source_compatible": True,
        },
    }
    encoded = json.dumps(
        layout,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    layout["sha256_without_this_field"] = hashlib.sha256(encoded).hexdigest()
    return layout


def hex_values(values: Iterable[int], width: int) -> str:
    return ", ".join(f"0x{value:0{width}X}" for value in values)


def emit_scalar_array(
    declaration: str,
    values: Sequence[int],
    columns: int = 16,
    width: int = 2,
) -> List[str]:
    lines = [declaration, "{"]
    for start in range(0, len(values), columns):
        lines.append(
            "\t" + hex_values(values[start:start + columns], width) + ","
        )
    lines.append("};")
    return lines


def emit_cpp(layout: Dict[str, object]) -> str:
    regular_layout = layout["regular"]  # type: ignore[index]
    transition_layout = layout["transition"]  # type: ignore[index]
    lines = [
        "// =============================================================",
        "// Research-only Transvoxel.cpp-compatible data surface.",
        "// Generated code/data is not yet cleared for an 0BSD release.",
        "// Internal class IDs are independent and may differ.",
        "// =============================================================",
        "",
        "struct RegularCellData",
        "{",
        "\tunsigned char geometryCounts;",
        "\tunsigned char vertexIndex[15];",
        "",
        "\tunsigned char get_vertex_index(unsigned int i) const { return vertexIndex[i]; }",
        "\tlong GetVertexCount(void) const { return (geometryCounts >> 4); }",
        "\tlong GetTriangleCount(void) const { return (geometryCounts & 0x0F); }",
        "};",
        "",
        "struct TransitionCellData",
        "{",
        "\tlong geometryCounts;",
        "\tunsigned char vertexIndex[36];",
        "",
        "\tunsigned char get_vertex_index(unsigned int i) const { return vertexIndex[i]; }",
        "\tlong GetVertexCount(void) const { return (geometryCounts >> 4); }",
        "\tlong GetTriangleCount(void) const { return (geometryCounts & 0x0F); }",
        "};",
        "",
    ]
    lines.extend(emit_scalar_array(
        "const unsigned char regularCellClass[256] =",
        regular_layout["case_class"],  # type: ignore[index]
    ))
    lines.extend(["", "const RegularCellData regularCellData[16] =", "{"])
    for record in regular_layout["class_data"]:  # type: ignore[index]
        geometry = (
            (int(record["vertex_count"]) << 4)
            | int(record["triangle_count"])
        )
        indices = record["indices"]
        lines.append(
            f"\t{{0x{geometry:02X}, "
            + ("{" + hex_values(indices, 2) + "}" if indices else "{}")
            + "},"
        )
    lines.extend(["};", "", "const unsigned short regularVertexData[256][12] =", "{"])
    for row in regular_layout["vertex_data"]:  # type: ignore[index]
        lines.append(
            "\t{" + hex_values(row, 4) + "},"
            if row else "\t{},"
        )
    lines.extend(["};", ""])
    lines.extend(emit_scalar_array(
        "const unsigned char transitionCellClass[512] =",
        transition_layout["case_class"],  # type: ignore[index]
    ))
    lines.extend(["", "const TransitionCellData transitionCellData[56] =", "{"])
    for record in transition_layout["class_data"]:  # type: ignore[index]
        geometry = (
            (int(record["vertex_count"]) << 4)
            | int(record["triangle_count"])
        )
        indices = record["indices"]
        lines.append(
            f"\t{{0x{geometry:02X}, "
            + ("{" + hex_values(indices, 2) + "}" if indices else "{}")
            + "},"
        )
    lines.extend(["};", ""])
    lines.extend(emit_scalar_array(
        "const unsigned char transitionCornerData[13] =",
        transition_layout["corner_data"],  # type: ignore[index]
        columns=13,
    ))
    lines.extend([
        "",
        "const unsigned short transitionVertexData[512][12] =",
        "{",
    ])
    for row in transition_layout["vertex_data"]:  # type: ignore[index]
        lines.append(
            "\t{" + hex_values(row, 4) + "},"
            if row else "\t{},"
        )
    lines.extend(["};", ""])
    return "\n".join(lines)


def decode_layout_case(
    layout: Dict[str, object],
    section_name: str,
    case_index: int,
) -> Tuple[List[Edge], List[IndexTriangle]]:
    section = layout[section_name]  # type: ignore[index]
    class_code = int(section["case_class"][case_index])  # type: ignore[index]
    flip = section_name == "transition" and bool(class_code & 0x80)
    class_id = class_code & 0x7F
    data = section["class_data"][class_id]  # type: ignore[index]
    vertex_count = int(data["vertex_count"])
    triangle_count = int(data["triangle_count"])
    row = section["vertex_data"][case_index]  # type: ignore[index]
    vertices = [
        ((int(code) & 0xFF) >> 4, int(code) & 0x0F)
        for code in row[:vertex_count]
    ]
    flat = [int(value) for value in data["indices"][:triangle_count * 3]]
    triangles = [
        (flat[index], flat[index + 1], flat[index + 2])
        for index in range(0, len(flat), 3)
    ]
    if flip:
        triangles = [(c, b, a) for a, b, c in triangles]
    return vertices, triangles


def semantic_report(
    layout: Dict[str, object],
    m24: Dict[str, object],
    oracle: Dict[str, object],
) -> Dict[str, object]:
    regular_matches = 0
    transition_matches = 0
    packed_multiset_matches = 0
    class_bounds_ok = True

    for case_index in range(256):
        vertices, triangles = decode_layout_case(
            layout,
            "regular",
            case_index,
        )
        expected_vertices, expected_triangles = (
            oracle_compare.case_from_export(m24["regular"], case_index)  # type: ignore[arg-type]
        )
        actual = oracle_compare.edge_triangles(vertices, triangles)
        expected = oracle_compare.edge_triangles(
            expected_vertices,
            expected_triangles,
        )
        if Counter(map(canonical_triangle, actual)) == Counter(
            map(canonical_triangle, expected)
        ):
            regular_matches += 1
        official_vertices, _official_triangles, _class_id = (
            oracle_compare.official_regular_case(oracle, case_index)
        )
        actual_codes = layout["regular"]["vertex_data"][case_index]  # type: ignore[index]
        official_codes = oracle["regular_vertices"][case_index]  # type: ignore[index]
        if Counter(actual_codes) == Counter(official_codes):
            packed_multiset_matches += 1
        class_bounds_ok = class_bounds_ok and (
            int(layout["regular"]["case_class"][case_index]) < 16  # type: ignore[index]
        )

    inverse_cases = layout["transition"]["official_case_to_local_case"]  # type: ignore[index]
    for official_case in range(512):
        local_case = int(inverse_cases[official_case])
        vertices, triangles = decode_layout_case(
            layout,
            "transition",
            official_case,
        )
        expected_vertices, expected_triangles = (
            oracle_compare.case_from_export(m24["transition"], local_case)  # type: ignore[arg-type]
        )
        actual = oracle_compare.edge_triangles(vertices, triangles)
        expected = oracle_compare.edge_triangles(
            expected_vertices,
            expected_triangles,
        )
        if Counter(map(canonical_triangle, actual)) == Counter(
            map(canonical_triangle, expected)
        ):
            transition_matches += 1
        actual_codes = layout["transition"]["vertex_data"][official_case]  # type: ignore[index]
        official_codes = oracle["transition_vertices"][official_case]  # type: ignore[index]
        if Counter(actual_codes) == Counter(official_codes):
            packed_multiset_matches += 1
        class_bounds_ok = class_bounds_ok and (
            (
                int(layout["transition"]["case_class"][official_case])  # type: ignore[index]
                & 0x7F
            )
            < 56
        )

    corner_exact = (
        layout["transition"]["corner_data"]  # type: ignore[index]
        == oracle["transition_corner_data"]
    )
    return {
        "regular_oriented_topology_matches": regular_matches,
        "transition_oriented_topology_matches": transition_matches,
        "packed_vertex_code_multiset_matches": packed_multiset_matches,
        "transition_corner_data_matches": corner_exact,
        "all_class_indexes_within_original_capacities": class_bounds_ok,
    }


def write_markdown(report: Dict[str, object]) -> None:
    metrics = report["metrics"]  # type: ignore[index]
    lines = [
        "# M25 Compatible Transvoxel.cpp Layout",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- Regular classes used/capacity: "
        f"`{metrics['regular_used_classes']}/16`",
        f"- Transition classes used/capacity: "
        f"`{metrics['transition_used_classes']}/56`",
        f"- Exact regular topology: "
        f"`{metrics['regular_oriented_topology_matches']}/256`",
        f"- Exact transition topology: "
        f"`{metrics['transition_oriented_topology_matches']}/512`",
        f"- Packed vertex-code multisets: "
        f"`{metrics['packed_vertex_code_multiset_matches']}/768`",
        f"- Transition corner reuse data exact: "
        f"`{metrics['transition_corner_data_matches']}`",
        "",
        "The generated research file preserves original struct names, symbol "
        "names, and array capacities. Internal numeric class IDs and table "
        "bytes intentionally differ.",
        "",
        "The generated data remains research-only because M24 topology "
        "selection provenance is not yet cleared for an 0BSD release.",
        "",
    ]
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    layout = build_layout()
    m24 = json.loads(M24_TABLES.read_text(encoding="utf-8"))
    oracle_path = oracle_compare.discover_oracle(None)
    oracle = oracle_compare.parse_oracle(oracle_path)
    metrics = semantic_report(layout, m24, oracle)
    metrics.update({
        "regular_used_classes": layout["regular"]["used_class_count"],  # type: ignore[index]
        "transition_used_classes": layout["transition"]["used_class_count"],  # type: ignore[index]
    })
    passed = (
        metrics["regular_oriented_topology_matches"] == 256
        and metrics["transition_oriented_topology_matches"] == 512
        and metrics["packed_vertex_code_multiset_matches"] == 768
        and metrics["transition_corner_data_matches"] is True
        and metrics["all_class_indexes_within_original_capacities"] is True
        and metrics["regular_used_classes"] <= 16
        and metrics["transition_used_classes"] <= 56
    )
    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.m25.compatible_layout_report.v1",
        "status": (
            "PASS_M25_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT"
            if passed else "FAIL_M25_COMPATIBLE_LAYOUT"
        ),
        "meaning": (
            "Original Transvoxel.cpp data ABI shapes with exact topology and "
            "formula-derived reuse semantics. Numeric class IDs and bytes are "
            "not claimed identical."
        ),
        "metrics": metrics,
        "decisions": {
            "compatible_struct_and_symbol_surface": passed,
            "packed_vertex_reuse_semantics": passed,
            "compatible_class_capacity_layout": passed,
            "official_numeric_class_ids_identical": False,
            "byte_identity": False,
            "generated_data_0bsd_provenance_cleared": False,
            "ready_for_unchanged_consumer_compile_test": passed,
            "exact_drop_in_replacement_ready": False,
        },
        "oracle": {
            "origin": oracle_compare.EXPECTED_ORIGIN,
            "commit": oracle_compare.EXPECTED_COMMIT,
            "sha256": hashlib.sha256(oracle_path.read_bytes()).hexdigest(),
            "used_for_validation_only": True,
        },
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    LAYOUT_PATH.write_text(
        json.dumps(layout, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    CPP_PATH.write_text(emit_cpp(layout), encoding="utf-8")
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("M25 compatible layout:", report["status"])
    print(
        "classes:",
        metrics["regular_used_classes"],
        "/ 16 regular,",
        metrics["transition_used_classes"],
        "/ 56 transition",
    )
    print(
        "topology:",
        metrics["regular_oriented_topology_matches"],
        "/ 256 regular,",
        metrics["transition_oriented_topology_matches"],
        "/ 512 transition",
    )
    print(CPP_PATH)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
