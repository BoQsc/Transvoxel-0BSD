#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate M4 runtime candidate topology tables.

The validation target is internal correctness of this repository's clean-room
candidate. This script does not compare against official MIT Transvoxel.cpp
table arrays.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[3]
M3_DIR = ROOT / "research" / "official_topology" / "m3"
M4_DIR = ROOT / "research" / "official_topology" / "m4"
GENERATED_DIR = ROOT / "generated"

sys.path.insert(0, str(M3_DIR))
sys.path.insert(0, str(M4_DIR))
import m3_core as m3  # noqa: E402
import generate_runtime_tables as generator  # noqa: E402

TABLE_PATH = GENERATED_DIR / "official_topology_candidate_tables.json"
HEADER_PATH = GENERATED_DIR / "official_topology_candidate_tables.h"
REPORT_PATH = M4_DIR / "runtime_table_validation.json"

Edge = Tuple[int, int]
Segment = Tuple[Edge, Edge]
Triangle = Tuple[Edge, Edge, Edge]


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def edge_from_json(value: Sequence[int]) -> Edge:
    a, b = int(value[0]), int(value[1])
    return (a, b) if a < b else (b, a)


def segment_from_json(value: Sequence[Sequence[int]]) -> Segment:
    return (edge_from_json(value[0]), edge_from_json(value[1]))


def triangle_edges_from_case(case: Dict[str, object]) -> List[Triangle]:
    vertices = [
        edge_from_json(vertex["samples"])  # type: ignore[index]
        for vertex in case["vertices"]  # type: ignore[index]
    ]
    result: List[Triangle] = []
    for triangle in case["triangles"]:  # type: ignore[index]
        ids = [int(v) for v in triangle["vertices"]]  # type: ignore[index]
        result.append((vertices[ids[0]], vertices[ids[1]], vertices[ids[2]]))
    return result


def validate_base_metadata(table: Dict[str, object]) -> List[str]:
    errors = []
    if table.get("schema") != generator.SCHEMA:
        errors.append("schema mismatch")
    if table.get("license") != "0BSD":
        errors.append("license is not 0BSD")
    if table.get("status") != generator.STATUS:
        errors.append("status mismatch")
    if table.get("official_transvoxel_cpp_byte_identity") != "NOT_PROVEN":
        errors.append("official byte identity claim must remain NOT_PROVEN")
    if table.get("official_triangle_topology_equivalence") != "NOT_PROVEN":
        errors.append("official topology equivalence claim must remain NOT_PROVEN")
    expected_sha = generator.table_sha_without_self(table)
    if table.get("sha256_without_this_field") != expected_sha:
        errors.append("sha256_without_this_field mismatch")
    return errors


def validate_transform(case: Dict[str, object], class_record: Dict[str, object]) -> List[str]:
    errors = []
    case_index = int(case["case"])
    representative = int(class_record["representative_case"])
    transform = case["transform_from_representative"]  # type: ignore[index]
    transform_id = int(transform["d4_transform"])  # type: ignore[index]
    complement = bool(transform["complement"])  # type: ignore[index]
    transformed_case = m3.apply_permutation(representative, m3.D4_PERMUTATIONS[transform_id])
    if complement:
        transformed_case ^= m3.CASE_MASK
    if transformed_case != case_index:
        errors.append(
            f"case {case_index}: transform maps representative "
            f"{representative} to {transformed_case}"
        )
    expected_flip = complement ^ generator.transform_parity_is_negative(transform_id)
    if bool(transform["orientation_flip"]) != expected_flip:  # type: ignore[index]
        errors.append(f"case {case_index}: orientation flip does not match transform parity")
    return errors


def validate_case_topology(case: Dict[str, object]) -> Dict[str, object]:
    case_index = int(case["case"])
    triangles = triangle_edges_from_case(case)
    expected_boundary = [
        segment
        for segments in m3.boundary_segments_by_face(case_index).values()
        for segment in segments
    ]
    validation = m3.validate_triangle_complex(triangles, expected_boundary)

    bad_vertex_pairs = []
    seen_vertices = set()
    duplicate_vertices = []
    for vertex in case["vertices"]:  # type: ignore[index]
        edge = edge_from_json(vertex["samples"])  # type: ignore[index]
        if edge in seen_vertices:
            duplicate_vertices.append(list(edge))
        seen_vertices.add(edge)
        if m3.sample_sign(case_index, edge[0]) == m3.sample_sign(case_index, edge[1]):
            bad_vertex_pairs.append(list(edge))

    bad_triangle_ids = []
    directed_edge_uses: Dict[
        Tuple[int, int],
        List[Tuple[int, int]],
    ] = {}
    vertex_count = len(case["vertices"])  # type: ignore[arg-type]
    for triangle_id, triangle in enumerate(case["triangles"]):  # type: ignore[index]
        ids = [int(v) for v in triangle["vertices"]]  # type: ignore[index]
        if len(ids) != 3 or len(set(ids)) != 3 or any(v < 0 or v >= vertex_count for v in ids):
            bad_triangle_ids.append(triangle_id)
            continue
        for a, b in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            key = (a, b) if a < b else (b, a)
            directed_edge_uses.setdefault(key, []).append((a, b))

    internal_winding_failures = [
        [list(edge) for edge in uses]
        for uses in directed_edge_uses.values()
        if len(uses) == 2 and uses[0] == uses[1]
    ]
    oriented_triangles = generator.orient_triangle_components(
        case_index,
        triangles,
    )
    outward_winding_matches = oriented_triangles == triangles

    status = (
        "PASS"
        if validation["status"] == "PASS"
        and not bad_vertex_pairs
        and not duplicate_vertices
        and not bad_triangle_ids
        and not internal_winding_failures
        and outward_winding_matches
        else "FAIL"
    )
    return {
        "status": status,
        "triangle_complex": validation,
        "bad_vertex_pairs": bad_vertex_pairs,
        "duplicate_vertices": duplicate_vertices,
        "bad_triangle_ids": bad_triangle_ids,
        "internal_winding_failures": internal_winding_failures,
        "outward_winding_matches": outward_winding_matches,
    }


def validate_flat_arrays(table: Dict[str, object]) -> List[str]:
    errors = []
    cases = table["cases"]  # type: ignore[index]
    flat = table["flat"]  # type: ignore[index]
    vertex_pairs = flat["vertex_pairs"]  # type: ignore[index]
    triangles = flat["triangles"]  # type: ignore[index]

    for case_index, case in enumerate(cases):
        vertex_start = int(flat["case_vertex_start"][case_index])  # type: ignore[index]
        vertex_count = int(flat["case_vertex_count"][case_index])  # type: ignore[index]
        triangle_start = int(flat["case_triangle_start"][case_index])  # type: ignore[index]
        triangle_count = int(flat["case_triangle_count"][case_index])  # type: ignore[index]
        expected_vertices = [
            vertex["samples"]  # type: ignore[index]
            for vertex in case["vertices"]  # type: ignore[index]
        ]
        expected_triangles = [
            triangle["vertices"]  # type: ignore[index]
            for triangle in case["triangles"]  # type: ignore[index]
        ]
        if vertex_pairs[vertex_start:vertex_start + vertex_count] != expected_vertices:
            errors.append(f"case {case_index}: flat vertex slice mismatch")
        if triangles[triangle_start:triangle_start + triangle_count] != expected_triangles:
            errors.append(f"case {case_index}: flat triangle slice mismatch")

    if len(vertex_pairs) != sum(int(case["vertex_count"]) for case in cases):
        errors.append("flat vertex pair count mismatch")
    if len(triangles) != sum(int(case["triangle_count"]) for case in cases):
        errors.append("flat triangle count mismatch")
    return errors


def validate_regeneration(table: Dict[str, object]) -> List[str]:
    regenerated = generator.generate_table()
    if regenerated != table:
        return ["regenerated table differs from generated/official_topology_candidate_tables.json"]
    expected_header = generator.emit_header(table)
    if not HEADER_PATH.exists():
        return ["generated/official_topology_candidate_tables.h is missing"]
    if HEADER_PATH.read_text(encoding="utf-8") != expected_header:
        return ["generated/official_topology_candidate_tables.h is stale"]
    return []


def validate_table(table: Dict[str, object]) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    errors.extend(validate_base_metadata(table))

    class_data = read_json(M3_DIR / "class_partition.json")
    expected_case_to_class = [
        int(value)
        for value in class_data["case_to_research_class"]  # type: ignore[index]
    ]

    cases = table.get("cases", [])
    classes = table.get("classes", [])
    if len(cases) != 512:
        errors.append(f"case count is {len(cases)}, expected 512")
    if len(classes) != 73:
        errors.append(f"research class count is {len(classes)}, expected 73")

    class_by_id = {
        int(record["research_class_id"]): record
        for record in classes  # type: ignore[union-attr]
    }
    case_failures = []
    topology_failures = []
    winding_failures = []
    triangle_counts = []
    vertex_counts = []
    transform_counter: Counter[str] = Counter()

    for expected_case_index, case in enumerate(cases):  # type: ignore[union-attr]
        case_index = int(case["case"])
        if case_index != expected_case_index:
            errors.append(f"case order mismatch at {expected_case_index}: found {case_index}")
            continue
        class_id = int(case["research_class_id"])
        if class_id != expected_case_to_class[case_index]:
            errors.append(f"case {case_index}: research class mismatch")
        class_record = class_by_id.get(class_id)
        if class_record is None:
            errors.append(f"case {case_index}: missing class {class_id}")
            continue
        transform_errors = validate_transform(case, class_record)
        if transform_errors:
            case_failures.extend(transform_errors)
        transform = case["transform_from_representative"]  # type: ignore[index]
        transform_counter[str(transform["d4_transform_name"])] += 1  # type: ignore[index]
        topology = validate_case_topology(case)
        if topology["status"] != "PASS":
            topology_failures.append({
                "case": case_index,
                "research_class_id": class_id,
                "topology": topology,
            })
        if (
            topology["internal_winding_failures"]
            or not topology["outward_winding_matches"]
        ):
            winding_failures.append(case_index)
        triangle_counts.append(int(case["triangle_count"]))
        vertex_counts.append(int(case["vertex_count"]))

    errors.extend(case_failures[:20])
    if len(case_failures) > 20:
        errors.append(f"{len(case_failures) - 20} additional transform failures omitted")
    if topology_failures:
        errors.append(f"{len(topology_failures)} case topology validations failed")

    errors.extend(validate_flat_arrays(table)[:20])
    errors.extend(validate_regeneration(table))

    return {
        "schema": "boqsc.transvoxel.official_topology.m4.validation.v1",
        "status": (
            "PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if not errors else "FAIL_M4_RUNTIME_TABLES"
        ),
        "ok": not errors,
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "errors": errors,
        "warnings": warnings,
        "case_count": len(cases),
        "research_class_count": len(classes),
        "case_topology_failure_count": len(topology_failures),
        "case_topology_failure_examples": topology_failures[:10],
        "case_winding_failure_count": len(winding_failures),
        "case_winding_failure_examples": winding_failures[:20],
        "transform_failure_count": len(case_failures),
        "transform_distribution": dict(sorted(transform_counter.items())),
        "triangle_count_histogram": {
            str(k): v for k, v in sorted(Counter(triangle_counts).items())
        },
        "vertex_count_histogram": {
            str(k): v for k, v in sorted(Counter(vertex_counts).items())
        },
        "total_triangles": sum(triangle_counts),
        "total_vertex_pairs": sum(vertex_counts),
        "sha256_without_this_field": table.get("sha256_without_this_field"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default=str(TABLE_PATH))
    parser.add_argument("--out", default=str(REPORT_PATH))
    args = parser.parse_args()

    table = read_json(Path(args.table))
    report = validate_table(table)
    write_json(Path(args.out), report)
    print("M4 runtime table validation:", Path(args.out))
    print("status:", report["status"])
    print("total triangles:", report["total_triangles"])
    print("total vertex pairs:", report["total_vertex_pairs"])
    if report["errors"]:
        print("errors:")
        for error in report["errors"]:
            print("-", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
