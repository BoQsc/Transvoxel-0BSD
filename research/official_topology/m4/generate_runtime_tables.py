#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Generate M4 runtime-ready candidate topology tables from M3 outputs.

This is a clean-room table generator. It consumes only this repository's M3
derived boundary-loop/candidate-triangulation data and symmetry rules. It does
not read, copy, compare, or tune against Eric Lengyel's MIT Transvoxel.cpp
lookup-table arrays.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[3]
M3_DIR = ROOT / "research" / "official_topology" / "m3"
GENERATED_DIR = ROOT / "generated"

sys.path.insert(0, str(M3_DIR))
import m3_core as m3  # noqa: E402

SCHEMA = "boqsc.transvoxel.official_topology.m4.runtime_candidate.v1"
LICENSE = "0BSD"
STATUS = "candidate_runtime_tables_official_equivalence_not_proven"

JSON_OUT = GENERATED_DIR / "official_topology_candidate_tables.json"
HEADER_OUT = GENERATED_DIR / "official_topology_candidate_tables.h"

Edge = Tuple[int, int]
Triangle = Tuple[Edge, Edge, Edge]

CORNER_FULL_TO_HALF = {full: half for half, full in m3.HALF_TO_FULL.items()}

D4_TRANSFORM_NAMES = {
    0: "identity",
    1: "rotate_90",
    2: "rotate_180",
    3: "rotate_270",
    4: "reflect_x",
    5: "reflect_x_then_rotate_90",
    6: "reflect_x_then_rotate_180",
    7: "reflect_x_then_rotate_270",
}


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(data: Dict[str, object]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_sha_without_self(table: Dict[str, object]) -> str:
    copy = dict(table)
    copy.pop("sha256_without_this_field", None)
    return hashlib.sha256(canonical_bytes(copy)).hexdigest()


def json_edge(value: Sequence[int]) -> Edge:
    a, b = int(value[0]), int(value[1])
    if a == b:
        raise ValueError(f"degenerate edge {value}")
    return (a, b) if a < b else (b, a)


def json_triangle(value: Sequence[Sequence[int]]) -> Triangle:
    return tuple(json_edge(edge) for edge in value)  # type: ignore[return-value]


def serialize_edge(edge: Edge) -> List[int]:
    return [edge[0], edge[1]]


def serialize_triangle(triangle: Triangle) -> List[List[int]]:
    return [serialize_edge(edge) for edge in triangle]


def sample_permutation(transform_id: int) -> Dict[int, int]:
    """Map sample ids 0..12 under the M3 D4 transform."""
    full_perm = m3.D4_PERMUTATIONS[transform_id]
    result = {sample_id: full_perm[sample_id] for sample_id in range(9)}
    for half_sample, full_corner in m3.HALF_TO_FULL.items():
        transformed_corner = full_perm[full_corner]
        result[half_sample] = CORNER_FULL_TO_HALF[transformed_corner]
    return result


def transform_edge(edge: Edge, transform_id: int) -> Edge:
    permutation = sample_permutation(transform_id)
    return json_edge((permutation[edge[0]], permutation[edge[1]]))


def transform_triangle(
    triangle: Triangle,
    transform_id: int,
    orientation_flip: bool,
) -> Triangle:
    transformed = tuple(transform_edge(edge, transform_id) for edge in triangle)
    if orientation_flip:
        transformed = tuple(reversed(transformed))
    return transformed  # type: ignore[return-value]


def transform_parity_is_negative(transform_id: int) -> bool:
    # The M3 D4 numbering applies a reflection first for ids 4..7.
    return transform_id >= 4


def find_case_transform(representative_case: int, case_index: int) -> Dict[str, object]:
    candidates: List[Tuple[bool, int]] = []
    for transform_id, permutation in enumerate(m3.D4_PERMUTATIONS):
        transformed = m3.apply_permutation(representative_case, permutation)
        if transformed == case_index:
            candidates.append((False, transform_id))
        if (transformed ^ m3.CASE_MASK) == case_index:
            candidates.append((True, transform_id))
    if not candidates:
        raise ValueError(
            f"no D4/complement transform maps representative "
            f"{representative_case} to case {case_index}"
        )
    complement, transform_id = min(candidates)
    orientation_flip = bool(complement) ^ transform_parity_is_negative(transform_id)
    return {
        "representative_case": representative_case,
        "d4_transform": transform_id,
        "d4_transform_name": D4_TRANSFORM_NAMES[transform_id],
        "complement": complement,
        "orientation_flip": orientation_flip,
    }


def remap_case_triangles(triangles: Sequence[Triangle]) -> Dict[str, object]:
    vertex_map: Dict[Edge, int] = {}
    vertices: List[Edge] = []
    remapped_triangles: List[Tuple[int, int, int]] = []
    for triangle in triangles:
        ids: List[int] = []
        for edge in triangle:
            if edge not in vertex_map:
                vertex_map[edge] = len(vertices)
                vertices.append(edge)
            ids.append(vertex_map[edge])
        remapped_triangles.append((ids[0], ids[1], ids[2]))
    return {
        "vertices": [
            {"id": vertex_id, "samples": serialize_edge(edge)}
            for vertex_id, edge in enumerate(vertices)
        ],
        "triangles": [
            {"vertices": [a, b, c]}
            for a, b, c in remapped_triangles
        ],
    }


def source_case_map(candidate_data: Dict[str, object]) -> Dict[int, Dict[str, object]]:
    return {
        int(record["case"]): record
        for record in candidate_data["cases"]  # type: ignore[index]
    }


def class_records(
    class_data: Dict[str, object],
    candidates: Dict[int, Dict[str, object]],
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for class_record in class_data["classes"]:  # type: ignore[index]
        class_id = int(class_record["research_class_id"])
        representative_case = int(class_record["representative_case"])
        source = candidates[representative_case]
        triangles = [
            json_triangle(value)
            for value in source["triangles"]  # type: ignore[index]
        ]
        remapped = remap_case_triangles(triangles)
        records.append({
            "research_class_id": class_id,
            "representative_case": representative_case,
            "source_kind": class_record["kind"],
            "inverse_research_class_id": class_record["inverse_research_class_id"],
            "source_base_research_class_id": class_record["source_base_research_class_id"],
            "ambiguity": class_record["ambiguity"],
            "case_count": class_record["class_size"],
            "cases": class_record["cases"],
            "vertex_count": len(remapped["vertices"]),  # type: ignore[arg-type]
            "triangle_count": len(remapped["triangles"]),  # type: ignore[arg-type]
            "vertices": remapped["vertices"],
            "triangles": remapped["triangles"],
        })
    return records


def class_triangles_as_edges(class_record: Dict[str, object]) -> List[Triangle]:
    vertices = [
        json_edge(vertex["samples"])  # type: ignore[index]
        for vertex in class_record["vertices"]  # type: ignore[index]
    ]
    result: List[Triangle] = []
    for triangle in class_record["triangles"]:  # type: ignore[index]
        ids = [int(value) for value in triangle["vertices"]]  # type: ignore[index]
        result.append((vertices[ids[0]], vertices[ids[1]], vertices[ids[2]]))
    return result


def case_records(
    class_data: Dict[str, object],
    class_table: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    case_to_class = [
        int(value)
        for value in class_data["case_to_research_class"]  # type: ignore[index]
    ]
    records: List[Dict[str, object]] = []
    for case_index, class_id in enumerate(case_to_class):
        cls = class_table[class_id]
        representative_case = int(cls["representative_case"])
        transform = find_case_transform(representative_case, case_index)
        class_triangles = class_triangles_as_edges(cls)
        transformed_triangles = [
            transform_triangle(
                triangle,
                int(transform["d4_transform"]),
                bool(transform["orientation_flip"]),
            )
            for triangle in class_triangles
        ]
        remapped = remap_case_triangles(transformed_triangles)
        records.append({
            "case": case_index,
            "inside_samples": [
                sample_id for sample_id in range(9)
                if m3.sample_sign(case_index, sample_id)
            ],
            "research_class_id": class_id,
            "transform_from_representative": transform,
            "ambiguity": m3.ambiguity_flags(case_index),
            "vertex_count": len(remapped["vertices"]),  # type: ignore[arg-type]
            "triangle_count": len(remapped["triangles"]),  # type: ignore[arg-type]
            "vertices": remapped["vertices"],
            "triangles": remapped["triangles"],
        })
    return records


def flatten_cases(cases: Sequence[Dict[str, object]]) -> Dict[str, object]:
    vertex_pairs: List[List[int]] = []
    triangles: List[List[int]] = []
    vertex_start: List[int] = []
    vertex_count: List[int] = []
    triangle_start: List[int] = []
    triangle_count: List[int] = []
    research_class: List[int] = []
    d4_transform: List[int] = []
    complement: List[int] = []
    orientation_flip: List[int] = []

    for case in cases:
        vertex_start.append(len(vertex_pairs))
        case_vertices = [
            list(vertex["samples"])  # type: ignore[index]
            for vertex in case["vertices"]  # type: ignore[index]
        ]
        vertex_pairs.extend(case_vertices)
        vertex_count.append(len(case_vertices))

        triangle_start.append(len(triangles))
        case_triangles = [
            list(triangle["vertices"])  # type: ignore[index]
            for triangle in case["triangles"]  # type: ignore[index]
        ]
        triangles.extend(case_triangles)
        triangle_count.append(len(case_triangles))

        research_class.append(int(case["research_class_id"]))
        transform = case["transform_from_representative"]  # type: ignore[index]
        d4_transform.append(int(transform["d4_transform"]))  # type: ignore[index]
        complement.append(1 if transform["complement"] else 0)  # type: ignore[index]
        orientation_flip.append(1 if transform["orientation_flip"] else 0)  # type: ignore[index]

    return {
        "case_research_class": research_class,
        "case_d4_transform": d4_transform,
        "case_complement": complement,
        "case_orientation_flip": orientation_flip,
        "case_vertex_start": vertex_start,
        "case_vertex_count": vertex_count,
        "case_triangle_start": triangle_start,
        "case_triangle_count": triangle_count,
        "vertex_pairs": vertex_pairs,
        "triangles": triangles,
    }


def sample_records() -> List[Dict[str, object]]:
    records = []
    for sample_id in sorted(m3.SAMPLE_POSITIONS):
        if sample_id <= 8:
            kind = "full_resolution_face"
            sign_source = sample_id
        else:
            kind = "half_resolution_face"
            sign_source = m3.HALF_TO_FULL[sample_id]
        records.append({
            "id": sample_id,
            "position": list(m3.SAMPLE_POSITIONS[sample_id]),
            "kind": kind,
            "sign_source": sign_source,
        })
    return records


def generate_table() -> Dict[str, object]:
    class_path = M3_DIR / "class_partition.json"
    candidate_path = M3_DIR / "candidate_triangulations.json"
    boundary_path = M3_DIR / "boundary_loops.json"
    class_data = read_json(class_path)
    candidate_data = read_json(candidate_path)
    candidates = source_case_map(candidate_data)

    classes = class_records(class_data, candidates)
    cases = case_records(class_data, classes)
    flat = flatten_cases(cases)

    table: Dict[str, object] = {
        "schema": SCHEMA,
        "license": LICENSE,
        "status": STATUS,
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "warning": (
            "M4 emits runtime-ready candidate tables derived from the M3 "
            "clean-room research topology. These are not copied from, tuned "
            "against, or claimed equivalent to Eric Lengyel's MIT "
            "Transvoxel.cpp tables."
        ),
        "source_inputs": {
            "class_partition": {
                "path": "research/official_topology/m3/class_partition.json",
                "sha256": sha256_file(class_path),
                "schema": class_data.get("schema"),
                "status": class_data.get("status"),
            },
            "candidate_triangulations": {
                "path": "research/official_topology/m3/candidate_triangulations.json",
                "sha256": sha256_file(candidate_path),
                "schema": candidate_data.get("schema"),
                "status": candidate_data.get("status"),
            },
            "boundary_loops": {
                "path": "research/official_topology/m3/boundary_loops.json",
                "sha256": sha256_file(boundary_path),
            },
        },
        "runtime_contract": {
            "case_count": 512,
            "research_class_count": 73,
            "sample_count": 13,
            "case_bits": {str(i): 1 << i for i in range(9)},
            "half_resolution_sign_sources": {
                str(k): v for k, v in sorted(m3.HALF_TO_FULL.items())
            },
            "vertex_encoding": (
                "Each runtime vertex is the interpolated crossing on a sample "
                "edge [sample_a, sample_b]."
            ),
            "triangle_encoding": (
                "Each triangle references local per-case vertex ids. "
                "Flat triangle ids are relative to the case vertex_start."
            ),
            "winding_rule": (
                "Triangles are generated from each research-class representative "
                "and transformed per case. Orientation is flipped for complemented "
                "cases and D4 reflections. This is deterministic but not an "
                "official Transvoxel.cpp winding-equivalence proof."
            ),
        },
        "d4_transforms": [
            {
                "id": transform_id,
                "name": D4_TRANSFORM_NAMES[transform_id],
                "sample_permutation": {
                    str(k): v for k, v in sample_permutation(transform_id).items()
                },
                "orientation_reversing": transform_parity_is_negative(transform_id),
            }
            for transform_id in range(8)
        ],
        "samples": sample_records(),
        "classes": classes,
        "cases": cases,
        "flat": flat,
        "statistics": {
            "case_count": len(cases),
            "research_class_count": len(classes),
            "non_empty_case_count": sum(1 for case in cases if case["triangle_count"]),
            "total_vertex_pairs": len(flat["vertex_pairs"]),  # type: ignore[arg-type]
            "total_triangles": len(flat["triangles"]),  # type: ignore[arg-type]
            "max_vertices_per_case": max(int(case["vertex_count"]) for case in cases),
            "max_triangles_per_case": max(int(case["triangle_count"]) for case in cases),
        },
    }
    table["sha256_without_this_field"] = table_sha_without_self(table)
    return table


def c_array(name: str, c_type: str, values: Iterable[int], columns: int = 16) -> str:
    values = list(values)
    lines = [f"static const {c_type} {name}[{len(values)}] = {{"]
    for i in range(0, len(values), columns):
        chunk = ", ".join(str(v) for v in values[i:i + columns])
        suffix = "," if i + columns < len(values) else ""
        lines.append(f"    {chunk}{suffix}")
    lines.append("};")
    return "\n".join(lines)


def c_array_2d(name: str, c_type: str, values: Sequence[Sequence[int]], width: int) -> str:
    lines = [f"static const {c_type} {name}[{len(values)}][{width}] = {{"]
    for i, row in enumerate(values):
        suffix = "," if i + 1 < len(values) else ""
        lines.append("    {" + ", ".join(str(int(v)) for v in row) + "}" + suffix)
    lines.append("};")
    return "\n".join(lines)


def emit_header(table: Dict[str, object]) -> str:
    flat = table["flat"]  # type: ignore[index]
    stats = table["statistics"]  # type: ignore[index]
    lines = [
        "/* SPDX-License-Identifier: 0BSD */",
        "/* Generated by research/official_topology/m4/generate_runtime_tables.py.",
        " * Do not edit by hand.",
        " * Clean-room M4 candidate; official Transvoxel.cpp equivalence is NOT_PROVEN.",
        " */",
        "#ifndef TRANSVOXEL_OFFICIAL_TOPOLOGY_CANDIDATE_TABLES_H",
        "#define TRANSVOXEL_OFFICIAL_TOPOLOGY_CANDIDATE_TABLES_H",
        "",
        "#include <stdint.h>",
        "",
        "#define OTC_M4_CASE_COUNT 512u",
        "#define OTC_M4_RESEARCH_CLASS_COUNT 73u",
        "#define OTC_M4_SAMPLE_COUNT 13u",
        f"#define OTC_M4_VERTEX_PAIR_COUNT {stats['total_vertex_pairs']}u",
        f"#define OTC_M4_TRIANGLE_COUNT {stats['total_triangles']}u",
        "",
        c_array("otc_m4_case_research_class", "uint8_t", flat["case_research_class"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_d4_transform", "uint8_t", flat["case_d4_transform"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_complement", "uint8_t", flat["case_complement"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_orientation_flip", "uint8_t", flat["case_orientation_flip"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_vertex_start", "uint16_t", flat["case_vertex_start"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_vertex_count", "uint8_t", flat["case_vertex_count"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_triangle_start", "uint16_t", flat["case_triangle_start"]),  # type: ignore[index]
        "",
        c_array("otc_m4_case_triangle_count", "uint8_t", flat["case_triangle_count"]),  # type: ignore[index]
        "",
        c_array_2d("otc_m4_vertex_pairs", "uint8_t", flat["vertex_pairs"], 2),  # type: ignore[index]
        "",
        c_array_2d("otc_m4_triangles", "uint8_t", flat["triangles"], 3),  # type: ignore[index]
        "",
        "#endif /* TRANSVOXEL_OFFICIAL_TOPOLOGY_CANDIDATE_TABLES_H */",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(table: Dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / JSON_OUT.name
    header_path = out_dir / HEADER_OUT.name
    json_path.write_text(
        json.dumps(table, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    header_path.write_text(emit_header(table), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(GENERATED_DIR))
    args = parser.parse_args()

    table = generate_table()
    out_dir = Path(args.out)
    write_outputs(table, out_dir)
    print("M4 runtime candidate table:", out_dir / JSON_OUT.name)
    print("M4 C header:", out_dir / HEADER_OUT.name)
    print("status:", table["status"])
    print("sha256:", table["sha256_without_this_field"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
