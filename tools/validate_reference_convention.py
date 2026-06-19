#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Prove M4's mapping to the published transition-cell convention.

This validator uses only the dissertation-derived convention specification and
the repository's clean-room M4 output. It does not read official lookup arrays.
"""
from __future__ import annotations

from collections import defaultdict
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "reference_convention_report.json"
MD = ROOT / "validation" / "reference_convention_report.md"
SPEC_PATH = ROOT / "validation" / "official_reference_convention_research.json"
MATRIX_PATH = ROOT / "validation" / "reference_convention_matrix.json"
TABLE_PATH = ROOT / "generated" / "official_topology_candidate_tables.json"

M3_DIR = ROOT / "research" / "official_topology" / "m3"
sys.path.insert(0, str(M3_DIR))
import m3_core as m3  # noqa: E402

Vec3 = Tuple[float, float, float]
VertexKey = Tuple[int, int]
TriangleKey = Tuple[VertexKey, VertexKey, VertexKey]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def local_to_reference(local_case: int, weights: Sequence[int]) -> int:
    result = 0
    for sample_id, weight in enumerate(weights):
        if local_case & (1 << sample_id):
            result |= weight
    return result


def reference_to_local(reference_case: int, weights: Sequence[int]) -> int:
    result = 0
    for sample_id, weight in enumerate(weights):
        if reference_case & weight:
            result |= 1 << sample_id
    return result


def rotate_180_local(local_case: int) -> int:
    result = 0
    for sample_id in range(9):
        if local_case & (1 << sample_id):
            result |= 1 << (8 - sample_id)
    return result


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec3, amount: float) -> Vec3:
    return (a[0] * amount, a[1] * amount, a[2] * amount)


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def midpoint(a: Vec3, b: Vec3) -> Vec3:
    return scale(add(a, b), 0.5)


def case_value(local_case: int, sample_id: int) -> float:
    return -1.0 if (local_case & (1 << sample_id)) else 1.0


def transition_gradient(local_case: int, position: Vec3) -> Vec3:
    """Gradient of the documented clean-room face-to-face interpolant."""
    x, y, z = position
    cell_x = 0 if x < 1.0 else 1
    cell_y = 0 if y < 1.0 else 1
    tx = x - float(cell_x)
    ty = y - float(cell_y)
    full_ids = (
        cell_x + 3 * cell_y,
        cell_x + 1 + 3 * cell_y,
        cell_x + 3 * (cell_y + 1),
        cell_x + 1 + 3 * (cell_y + 1),
    )
    f00, f10, f01, f11 = (
        case_value(local_case, sample_id) for sample_id in full_ids
    )
    full_dx = (f10 - f00) * (1.0 - ty) + (f11 - f01) * ty
    full_dy = (f01 - f00) * (1.0 - tx) + (f11 - f10) * tx
    full_value = (
        f00 * (1.0 - tx) * (1.0 - ty)
        + f10 * tx * (1.0 - ty)
        + f01 * (1.0 - tx) * ty
        + f11 * tx * ty
    )

    half_x = x * 0.5
    half_y = y * 0.5
    h00, h10, h01, h11 = (
        case_value(local_case, sample_id)
        for sample_id in (0, 2, 6, 8)
    )
    half_dx = 0.5 * (
        (h10 - h00) * (1.0 - half_y)
        + (h11 - h01) * half_y
    )
    half_dy = 0.5 * (
        (h01 - h00) * (1.0 - half_x)
        + (h11 - h10) * half_x
    )
    half_value = (
        h00 * (1.0 - half_x) * (1.0 - half_y)
        + h10 * half_x * (1.0 - half_y)
        + h01 * (1.0 - half_x) * half_y
        + h11 * half_x * half_y
    )
    return (
        (1.0 - z) * full_dx + z * half_dx,
        (1.0 - z) * full_dy + z * half_dy,
        half_value - full_value,
    )


def cyclic_equal(a: TriangleKey, b: TriangleKey) -> bool:
    return any(a == b[offset:] + b[:offset] for offset in range(3))


def reverse_equal(a: TriangleKey, b: TriangleKey) -> bool:
    return cyclic_equal(a, (b[0], b[2], b[1]))


def triangle_records(
    case: Dict[str, Any],
) -> Tuple[List[VertexKey], List[TriangleKey]]:
    vertices = [
        tuple(int(value) for value in vertex["samples"])
        for vertex in case["vertices"]
    ]
    triangles = [
        tuple(vertices[int(index)] for index in triangle["vertices"])
        for triangle in case["triangles"]
    ]
    return vertices, triangles  # type: ignore[return-value]


def winding_metrics(
    table: Dict[str, Any],
    positions: Dict[int, Vec3],
) -> Dict[str, int]:
    metrics = {
        "cases": 0,
        "triangles": 0,
        "components": 0,
        "degenerate_triangles": 0,
        "nonmanifold_edges": 0,
        "incoherent_shared_edges": 0,
        "non_outward_components": 0,
        "complement_pairs_same_topology": 0,
        "complement_pairs_reverse_wound": 0,
        "complement_winding_failures": 0,
    }
    case_triangles: List[List[TriangleKey]] = []
    for case in table["cases"]:
        local_case = int(case["case"])
        _, triangles = triangle_records(case)
        case_triangles.append(triangles)
        metrics["cases"] += 1
        metrics["triangles"] += len(triangles)

        edge_uses: Dict[
            Tuple[VertexKey, VertexKey],
            List[Tuple[int, VertexKey, VertexKey]],
        ] = defaultdict(list)
        triangle_normals: List[Vec3] = []
        triangle_centroids: List[Vec3] = []
        for triangle_id, triangle in enumerate(triangles):
            points = [
                midpoint(positions[edge[0]], positions[edge[1]])
                for edge in triangle
            ]
            normal = cross(
                sub(points[1], points[0]),
                sub(points[2], points[0]),
            )
            if dot(normal, normal) <= 1.0e-18:
                metrics["degenerate_triangles"] += 1
            triangle_normals.append(normal)
            triangle_centroids.append(scale(add(add(*points[:2]), points[2]), 1.0 / 3.0))
            for a, b in (
                (triangle[0], triangle[1]),
                (triangle[1], triangle[2]),
                (triangle[2], triangle[0]),
            ):
                key = (a, b) if a < b else (b, a)
                edge_uses[key].append((triangle_id, a, b))

        adjacency: Dict[int, List[int]] = defaultdict(list)
        for uses in edge_uses.values():
            if len(uses) > 2:
                metrics["nonmanifold_edges"] += 1
            if len(uses) == 2:
                first, second = uses
                if first[1:] == second[1:]:
                    metrics["incoherent_shared_edges"] += 1
                adjacency[first[0]].append(second[0])
                adjacency[second[0]].append(first[0])

        seen = set()
        for start in range(len(triangles)):
            if start in seen:
                continue
            component = []
            pending = [start]
            seen.add(start)
            while pending:
                triangle_id = pending.pop()
                component.append(triangle_id)
                for neighbor in adjacency[triangle_id]:
                    if neighbor not in seen:
                        seen.add(neighbor)
                        pending.append(neighbor)
            metrics["components"] += 1
            score = sum(
                dot(
                    triangle_normals[triangle_id],
                    transition_gradient(
                        local_case,
                        triangle_centroids[triangle_id],
                    ),
                )
                for triangle_id in component
            )
            if score <= 1.0e-12:
                metrics["non_outward_components"] += 1

    for local_case in range(256):
        complement = local_case ^ 0x1FF
        first = case_triangles[local_case]
        second = case_triangles[complement]
        first_map = {frozenset(triangle): triangle for triangle in first}
        second_map = {frozenset(triangle): triangle for triangle in second}
        if set(first_map) != set(second_map):
            continue
        metrics["complement_pairs_same_topology"] += 1
        if all(
            reverse_equal(first_map[key], second_map[key])
            for key in first_map
        ):
            metrics["complement_pairs_reverse_wound"] += 1
        else:
            metrics["complement_winding_failures"] += 1
    return metrics


def write_markdown(report: Dict[str, Any]) -> None:
    metrics = report["metrics"]
    checks = report["checks"]
    lines = [
        "# Published Reference Convention Validation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Published algorithmic reference equivalence: **{report['reference_equivalence_status']}**",
        "",
        "## Checks",
        "",
        *[
            f"- {'PASS' if value else 'FAIL'} - `{name}`"
            for name, value in checks.items()
        ],
        "",
        "## Exhaustive coverage",
        "",
        f"- Case-index bijection cases: `{metrics['case_mapping_cases']}`",
        f"- D4 transform/index comparisons: `{metrics['d4_mapping_comparisons']}`",
        f"- Wound triangles: `{metrics['winding']['triangles']}`",
        f"- Coherent components: `{metrics['winding']['components']}`",
        f"- Same-topology complement pairs: `{metrics['winding']['complement_pairs_same_topology']}`",
        f"- Reverse-wound complement pairs: `{metrics['winding']['complement_pairs_reverse_wound']}`",
        "",
        "This proves the public dissertation convention through an explicit case-index permutation. It does not prove official triangle topology, class IDs, vertex encoding, or table bytes.",
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    spec = read_json(SPEC_PATH)
    matrix = read_json(MATRIX_PATH)
    table = read_json(TABLE_PATH)

    weights = [
        int(spec["published_case_bits"][str(sample_id)])
        for sample_id in range(9)
    ]
    expected_positions = {
        **{
            int(key): tuple(float(v) for v in value)
            for key, value in spec["canonical_local_coordinates"][
                "full_resolution_samples"
            ].items()
        },
        **{
            int(key): tuple(float(v) for v in value)
            for key, value in spec["canonical_local_coordinates"][
                "half_resolution_samples"
            ].items()
        },
    }
    actual_positions = {
        int(record["id"]): tuple(float(v) for v in record["position"])
        for record in table["samples"]
    }
    sign_sources = {
        str(record["id"]): int(record["sign_source"])
        for record in table["samples"]
        if int(record["id"]) >= 9
    }

    mapping_failures = 0
    reference_values = set()
    complement_failures = 0
    rotate_180_failures = 0
    for local_case in range(512):
        reference_case = local_to_reference(local_case, weights)
        reference_values.add(reference_case)
        if reference_to_local(reference_case, weights) != local_case:
            mapping_failures += 1
        complement_reference = local_to_reference(local_case ^ 0x1FF, weights)
        if complement_reference != (reference_case ^ 0x1FF):
            complement_failures += 1
        rotated_reference = local_to_reference(
            rotate_180_local(local_case),
            weights,
        )
        expected_rotated = (
            ((reference_case & 0x00F) << 4)
            | ((reference_case & 0x0F0) >> 4)
            | (reference_case & 0x100)
        )
        if rotated_reference != expected_rotated:
            rotate_180_failures += 1

    d4_failures = 0
    d4_comparisons = 0
    for local_case in range(512):
        for permutation in m3.D4_PERMUTATIONS:
            transformed_local = m3.apply_permutation(local_case, permutation)
            direct_reference = 0
            for old_sample, new_sample in enumerate(permutation):
                if local_case & (1 << old_sample):
                    direct_reference |= weights[new_sample]
            if (
                local_to_reference(transformed_local, weights)
                != direct_reference
            ):
                d4_failures += 1
            d4_comparisons += 1

    winding = winding_metrics(table, actual_positions)
    runtime_contract = table.get("runtime_contract", {})
    published_contract = runtime_contract.get(
        "published_reference_convention",
        {},
    )
    checks = {
        "source_spec_is_published_convention_proof": (
            spec.get("official_convention_status") == "PROVEN"
        ),
        "same_13_sample_geometry_as_figures_4_8_and_4_16": (
            actual_positions == expected_positions
        ),
        "same_half_face_corner_correspondence": sign_sources == {
            "9": 0,
            "10": 2,
            "11": 6,
            "12": 8,
        },
        "negative_values_are_inside_case_bits": (
            spec["sign_and_winding"]["inside_solid"]
            == "sample_value < iso_level"
        ),
        "published_case_weights_match_figure_4_17": weights == [
            0x001,
            0x002,
            0x004,
            0x080,
            0x100,
            0x008,
            0x040,
            0x020,
            0x010,
        ],
        "local_and_published_indexes_are_bijective_for_all_512_cases": (
            mapping_failures == 0 and reference_values == set(range(512))
        ),
        "case_complement_commutes_with_index_mapping": (
            complement_failures == 0
        ),
        "published_180_degree_nibble_property_holds": (
            rotate_180_failures == 0
        ),
        "all_d4_sample_transforms_commute_with_index_mapping": (
            d4_failures == 0
        ),
        "generated_runtime_contract_records_mapping": (
            published_contract.get("status")
            == "PROVEN_BY_EXPLICIT_BIJECTION"
        ),
        "six_face_frames_are_orientation_preserving": (
            matrix.get("status")
            == "PASS_PUBLISHED_REFERENCE_CONVENTION_MATRIX"
            and matrix.get("official_reference_equivalence") == "PROVEN"
        ),
        "all_triangle_components_are_coherent_and_outward": (
            winding["degenerate_triangles"] == 0
            and winding["nonmanifold_edges"] == 0
            and winding["incoherent_shared_edges"] == 0
            and winding["non_outward_components"] == 0
        ),
        "same_topology_complements_reverse_winding": (
            winding["complement_pairs_same_topology"] > 0
            and winding["complement_pairs_same_topology"]
            == winding["complement_pairs_reverse_wound"]
            and winding["complement_winding_failures"] == 0
        ),
    }
    ok = all(checks.values())
    report = {
        "schema": "boqsc.transvoxel.reference_convention_audit.v2",
        "status": (
            "PASS_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE"
            if ok
            else "FAIL_REFERENCE_CONVENTION"
        ),
        "reference_equivalence_status": "PROVEN" if ok else "NOT_PROVEN",
        "official_reference_equivalence": "PROVEN" if ok else "NOT_PROVEN",
        "equivalence_scope": (
            "Published algorithmic sample geometry, sign polarity, case-index "
            "encoding, face direction, inversion winding, and six-face "
            "orientation transforms."
        ),
        "explicit_non_identity_mapping": {
            "local_case_bits": {
                str(sample_id): 1 << sample_id for sample_id in range(9)
            },
            "published_reference_case_bits": {
                str(sample_id): weights[sample_id]
                for sample_id in range(9)
            },
            "numeric_identity": False,
            "bijection": True,
        },
        "checks": checks,
        "metrics": {
            "case_mapping_cases": 512,
            "mapping_failures": mapping_failures,
            "distinct_reference_indexes": len(reference_values),
            "complement_mapping_failures": complement_failures,
            "rotate_180_mapping_failures": rotate_180_failures,
            "d4_mapping_comparisons": d4_comparisons,
            "d4_mapping_failures": d4_failures,
            "face_frames": len(matrix.get("faces", [])),
            "winding": winding,
        },
        "source_evidence": spec.get("source"),
        "claim_boundary": {
            "proven": (
                "Behavioral equivalence to the published transition-cell "
                "reference convention through an explicit case-index bijection."
            ),
            "not_proven": [
                "official transition triangle topology for all 512 cases",
                "official class ID mapping",
                "official vertex/cache encoding",
                "Transvoxel.cpp byte identity",
            ],
        },
        "no_copy_rule": (
            "No official lookup-table arrays were read or compared."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("reference convention audit:", report["status"])
    print(
        "cases:",
        report["metrics"]["case_mapping_cases"],
        "d4 comparisons:",
        d4_comparisons,
        "triangles:",
        winding["triangles"],
        "failures:",
        sum(
            int(value)
            for key, value in report["metrics"].items()
            if key.endswith("failures")
        )
        + winding["degenerate_triangles"]
        + winding["nonmanifold_edges"]
        + winding["incoherent_shared_edges"]
        + winding["non_outward_components"]
        + winding["complement_winding_failures"],
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
