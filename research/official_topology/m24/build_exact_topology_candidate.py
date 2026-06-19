#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build the M24 exact-topology research candidate.

The external MIT source is used only to select indexes from independently
enumerated clean-room triangulations. The committed rule file contains those
selection indexes and provenance hashes, not copied table arrays or packed
vertex/reuse codes.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[3]
M24_DIR = ROOT / "research" / "official_topology" / "m24"
GENERATED_DIR = M24_DIR / "generated"
RULES_PATH = M24_DIR / "topology_rules.json"
TABLES_PATH = GENERATED_DIR / "m24_exact_topology_tables.json"
HEADER_PATH = GENERATED_DIR / "m24_exact_topology_tables.h"
REPORT_PATH = ROOT / "validation" / "m24_exact_topology_report.json"
REPORT_MD_PATH = ROOT / "validation" / "m24_exact_topology_report.md"

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "research" / "official_topology" / "m3"))
sys.path.insert(0, str(ROOT / "research" / "official_topology" / "m4"))

import compare_official_oracle as oracle_compare  # noqa: E402
import export_transvoxel  # noqa: E402
import generate_regular as regular  # noqa: E402
import m3_core as m3  # noqa: E402


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m4 = load_module(
    "m24_m4_generator",
    ROOT / "research" / "official_topology" / "m4" / "generate_runtime_tables.py",
)

Edge = Tuple[int, int]
Triangle = Tuple[Edge, Edge, Edge]


def canonical_triangle_set(
    triangles: Iterable[Triangle],
) -> Tuple[Tuple[Edge, Edge, Edge], ...]:
    return tuple(sorted(tuple(sorted(triangle)) for triangle in triangles))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def json_edge(edge: Edge) -> List[int]:
    return [edge[0], edge[1]]


def json_triangle(triangle: Triangle) -> List[List[int]]:
    return [json_edge(edge) for edge in triangle]


def regular_boundary(case_index: int) -> Tuple[List[Any], List[Tuple[Edge, ...]]]:
    segments = regular.boundary_segments(case_index)
    loop_report = m3.trace_boundary_loops(segments)
    if loop_report["status"] != "PASS":
        raise ValueError(f"regular case {case_index}: boundary loop failure")
    return segments, list(loop_report["loops"])


def official_regular_triangles(
    oracle: Dict[str, object],
    case_index: int,
) -> List[Triangle]:
    vertices, triangles, _class_id = oracle_compare.official_regular_case(
        oracle,
        case_index,
    )
    return oracle_compare.edge_triangles(vertices, triangles)


def official_transition_triangles(
    oracle: Dict[str, object],
    local_case: int,
) -> List[Triangle]:
    official_case = oracle_compare.local_transition_to_official_case(local_case)
    vertices, raw, _runtime, _class_id, _inverted = (
        oracle_compare.official_transition_case(oracle, official_case)
    )
    return oracle_compare.edge_triangles(vertices, raw)


def option_index(loop: Sequence[Edge], target: Sequence[Triangle]) -> int:
    target_key = canonical_triangle_set(target)
    options = m3.all_loop_triangulations(loop)
    for index, option in enumerate(options):
        if canonical_triangle_set(option) == target_key:
            return index
    raise ValueError(
        f"target triangulation is not in clean-room enumeration for loop {loop}"
    )


def normalize_annulus_loops(
    loops: Sequence[Sequence[Edge]],
) -> Tuple[Tuple[Edge, ...], Tuple[Edge, ...]]:
    outer = tuple(loops[0])
    inner = tuple(loops[1])
    outer_points = [
        (m3.edge_position(vertex)[0], m3.edge_position(vertex)[1])
        for vertex in outer
    ]
    inner_points = [
        (m3.edge_position(vertex)[0], m3.edge_position(vertex)[1])
        for vertex in inner
    ]
    if abs(m3.polygon_area(outer_points)) < abs(
        m3.polygon_area(inner_points)
    ):
        outer, inner = inner, outer
        outer_points, inner_points = inner_points, outer_points
    if m3.polygon_area(outer_points) < 0:
        outer = tuple(reversed(outer))
    return outer, inner


def annulus_from_signature(
    loops: Sequence[Sequence[Edge]],
    signature: Dict[str, object],
) -> List[Triangle]:
    outer, inner = normalize_annulus_loops(loops)
    outer_direction = int(signature["outer_direction"])
    inner_direction = int(signature["inner_direction"])
    outer_start = int(signature["outer_start"])
    inner_start = int(signature["inner_start"])
    outer_steps = {int(value) for value in signature["outer_steps"]}
    ordered_outer = [
        outer[
            (outer_start + outer_direction * index) % len(outer)
        ]
        for index in range(len(outer))
    ]
    ordered_inner = [
        inner[
            (inner_start + inner_direction * index) % len(inner)
        ]
        for index in range(len(inner))
    ]
    outer_index = 0
    inner_index = 0
    triangles: List[Triangle] = []
    for step in range(len(ordered_outer) + len(ordered_inner)):
        current_outer = ordered_outer[outer_index % len(ordered_outer)]
        current_inner = ordered_inner[inner_index % len(ordered_inner)]
        if step in outer_steps:
            next_outer = ordered_outer[
                (outer_index + 1) % len(ordered_outer)
            ]
            triangle = m3.triangle_key(
                current_outer,
                next_outer,
                current_inner,
            )
            outer_index += 1
        else:
            next_inner = ordered_inner[
                (inner_index + 1) % len(ordered_inner)
            ]
            triangle = m3.triangle_key(
                current_outer,
                next_inner,
                current_inner,
            )
            inner_index += 1
        if m3.triangle_area_squared(triangle) <= 1.0e-12:
            raise ValueError("annulus signature produced a degenerate triangle")
        triangles.append(triangle)
    return triangles


def derive_annulus_signature(
    loops: Sequence[Sequence[Edge]],
    target: Sequence[Triangle],
) -> Dict[str, object]:
    outer, inner = normalize_annulus_loops(loops)
    target_key = canonical_triangle_set(target)
    signatures = []
    for outer_direction in (1, -1):
        for inner_direction in (1, -1):
            for outer_start in range(len(outer)):
                for inner_start in range(len(inner)):
                    step_count = len(outer) + len(inner)
                    for outer_steps in itertools.combinations(
                        range(step_count),
                        len(outer),
                    ):
                        signature = {
                            "outer_direction": outer_direction,
                            "inner_direction": inner_direction,
                            "outer_start": outer_start,
                            "inner_start": inner_start,
                            "outer_steps": list(outer_steps),
                        }
                        try:
                            triangles = annulus_from_signature(
                                loops,
                                signature,
                            )
                        except ValueError:
                            continue
                        if canonical_triangle_set(triangles) == target_key:
                            signatures.append(signature)
    if not signatures:
        raise ValueError("official annulus is not in clean-room zipper space")
    return min(
        signatures,
        key=lambda item: (
            int(item["outer_direction"]),
            int(item["inner_direction"]),
            int(item["outer_start"]),
            int(item["inner_start"]),
            tuple(int(value) for value in item["outer_steps"]),
        ),
    )


def derive_rules(
    oracle_path: Path,
    oracle: Dict[str, object],
) -> Dict[str, object]:
    old_positions = m3.SAMPLE_POSITIONS
    m3.SAMPLE_POSITIONS = {
        sample_id: tuple(float(value) for value in position)
        for sample_id, position in regular.SAMPLE_POSITIONS.items()
    }
    regular_rules = []
    try:
        for case_index in range(256):
            _segments, loops = regular_boundary(case_index)
            official = official_regular_triangles(oracle, case_index)
            indexes = []
            for loop in loops:
                target = [
                    triangle
                    for triangle in official
                    if set(triangle) <= set(loop)
                ]
                indexes.append(option_index(loop, target))
            regular_rules.append({
                "case": case_index,
                "loop_lengths": [len(loop) for loop in loops],
                "option_indexes": indexes,
            })
    finally:
        m3.SAMPLE_POSITIONS = old_positions

    partition_path = (
        ROOT
        / "research"
        / "official_topology"
        / "m3"
        / "class_partition.json"
    )
    partition = json.loads(partition_path.read_text(encoding="utf-8"))
    transition_rules = []
    for class_record in partition["classes"]:
        class_id = int(class_record["research_class_id"])
        representative = int(class_record["representative_case"])
        record = m3.derive_case_candidate(representative)
        loops = list(record["loops"])
        official = official_transition_triangles(oracle, representative)
        rule: Dict[str, object] = {
            "research_class_id": class_id,
            "representative_case": representative,
            "loop_lengths": [len(loop) for loop in loops],
        }
        if record["nesting"]:
            rule["kind"] = "planar_annulus_zipper"
            rule["annulus_signature"] = derive_annulus_signature(
                loops,
                official,
            )
        else:
            indexes = []
            for loop in loops:
                target = [
                    triangle
                    for triangle in official
                    if set(triangle) <= set(loop)
                ]
                indexes.append(option_index(loop, target))
            rule["kind"] = "independent_boundary_loops"
            rule["option_indexes"] = indexes
        transition_rules.append(rule)

    rules: Dict[str, object] = {
        "schema": "boqsc.transvoxel.m24.topology_rules.v1",
        "status": "ORACLE_CALIBRATED_CLEAN_ROOM_TRIANGULATION_SELECTIONS",
        "generator_code_license": "0BSD",
        "license": "MIT",
        "license_file": "LICENSES/MIT.txt",
        "copyright": "Copyright (c) 2009 Eric Lengyel",
        "generated_rule_license_status": "MIT_EXACT_COMPATIBILITY_DATA",
        "meaning": (
            "Clean-room boundary loops are triangulated by indexes into a "
            "deterministic independent enumeration. The external oracle is "
            "used only to calibrate those indexes."
        ),
        "oracle": {
            "origin": oracle_compare.EXPECTED_ORIGIN,
            "commit": oracle_compare.EXPECTED_COMMIT,
            "sha256": sha256_file(oracle_path),
            "arrays_copied": False,
            "packed_vertex_codes_copied": False,
        },
        "inputs": {
            "regular_generator_sha256": sha256_file(
                ROOT / "tools" / "generate_regular.py"
            ),
            "m3_core_sha256": sha256_file(
                ROOT
                / "research"
                / "official_topology"
                / "m3"
                / "m3_core.py"
            ),
            "class_partition_sha256": sha256_file(partition_path),
        },
        "regular": {
            "case_count": 256,
            "rules": regular_rules,
        },
        "transition": {
            "case_count": 512,
            "research_class_count": 73,
            "rules": transition_rules,
        },
    }
    rules["sha256_without_this_field"] = canonical_sha(rules)
    return rules


def regular_cases(rules: Dict[str, object]) -> List[Dict[str, object]]:
    rule_by_case = {
        int(record["case"]): record
        for record in rules["regular"]["rules"]  # type: ignore[index]
    }
    old_positions = m3.SAMPLE_POSITIONS
    m3.SAMPLE_POSITIONS = {
        sample_id: tuple(float(value) for value in position)
        for sample_id, position in regular.SAMPLE_POSITIONS.items()
    }
    cases = []
    try:
        for case_index in range(256):
            segments, loops = regular_boundary(case_index)
            rule = rule_by_case[case_index]
            indexes = [
                int(value) for value in rule["option_indexes"]  # type: ignore[index]
            ]
            if len(indexes) != len(loops):
                raise ValueError(
                    f"regular case {case_index}: rule/loop count mismatch"
                )
            triangles: List[Triangle] = []
            for loop, index in zip(loops, indexes):
                options = m3.all_loop_triangulations(loop)
                if not 0 <= index < len(options):
                    raise ValueError(
                        f"regular case {case_index}: bad option {index}"
                    )
                triangles.extend(options[index])
            validation = m3.validate_triangle_complex(triangles, segments)
            if validation["status"] != "PASS":
                raise ValueError(
                    f"regular case {case_index}: invalid complex {validation}"
                )
            triangles = regular.orient_components(case_index, triangles)
            vertices = sorted({
                vertex for triangle in triangles for vertex in triangle
            })
            vertex_map = {
                vertex: vertex_id
                for vertex_id, vertex in enumerate(vertices)
            }
            cases.append({
                "case": case_index,
                "vertices": [
                    {"id": vertex_id, "samples": json_edge(vertex)}
                    for vertex_id, vertex in enumerate(vertices)
                ],
                "triangles": [
                    {
                        "vertices": [
                            vertex_map[triangle[0]],
                            vertex_map[triangle[1]],
                            vertex_map[triangle[2]],
                        ]
                    }
                    for triangle in triangles
                ],
            })
    finally:
        m3.SAMPLE_POSITIONS = old_positions
    return cases


def transition_cases(rules: Dict[str, object]) -> List[Dict[str, object]]:
    partition = json.loads(
        (
            ROOT
            / "research"
            / "official_topology"
            / "m3"
            / "class_partition.json"
        ).read_text(encoding="utf-8")
    )
    rule_by_class = {
        int(record["research_class_id"]): record
        for record in rules["transition"]["rules"]  # type: ignore[index]
    }
    class_triangles: Dict[int, List[Triangle]] = {}
    for class_record in partition["classes"]:
        class_id = int(class_record["research_class_id"])
        representative = int(class_record["representative_case"])
        record = m3.derive_case_candidate(representative)
        loops = list(record["loops"])
        rule = rule_by_class[class_id]
        if rule["kind"] == "planar_annulus_zipper":
            triangles = annulus_from_signature(
                loops,
                rule["annulus_signature"],  # type: ignore[index]
            )
        else:
            indexes = [
                int(value)
                for value in rule["option_indexes"]  # type: ignore[index]
            ]
            if len(indexes) != len(loops):
                raise ValueError(
                    f"transition class {class_id}: rule/loop count mismatch"
                )
            triangles = []
            for loop, index in zip(loops, indexes):
                options = m3.all_loop_triangulations(loop)
                if not 0 <= index < len(options):
                    raise ValueError(
                        f"transition class {class_id}: bad option {index}"
                    )
                triangles.extend(options[index])
        validation = m3.validate_triangle_complex(
            triangles,
            record["segments"],
        )
        if validation["status"] != "PASS":
            raise ValueError(
                f"transition class {class_id}: invalid complex {validation}"
            )
        class_triangles[class_id] = m4.orient_triangle_components(
            representative,
            triangles,
        )

    case_to_class = [
        int(value) for value in partition["case_to_research_class"]
    ]
    cases = []
    for case_index, class_id in enumerate(case_to_class):
        representative = int(
            partition["classes"][class_id]["representative_case"]
        )
        transform = m4.find_case_transform(representative, case_index)
        triangles = [
            m4.transform_triangle(
                triangle,
                int(transform["d4_transform"]),
                bool(transform["orientation_flip"]),
            )
            for triangle in class_triangles[class_id]
        ]
        triangles = m4.orient_triangle_components(case_index, triangles)
        remapped = m4.remap_case_triangles(triangles)
        cases.append({
            "case": case_index,
            "research_class_id": class_id,
            "vertices": remapped["vertices"],
            "triangles": remapped["triangles"],
        })
    return cases


def compare_section(
    oracle: Dict[str, object],
    section: Dict[str, object],
    kind: str,
) -> Dict[str, object]:
    case_count = 256 if kind == "regular" else 512
    results = []
    for local_case in range(case_count):
        local_vertices, local_triangles = oracle_compare.case_from_export(
            section,
            local_case,
        )
        if kind == "regular":
            official_vertices, official_triangles, class_id = (
                oracle_compare.official_regular_case(oracle, local_case)
            )
            official_case = local_case
            inverted = False
            runtime = official_triangles
        else:
            official_case = (
                oracle_compare.local_transition_to_official_case(local_case)
            )
            (
                official_vertices,
                official_triangles,
                runtime,
                class_id,
                inverted,
            ) = oracle_compare.official_transition_case(
                oracle,
                official_case,
            )
        results.append(oracle_compare.compare_case(
            local_case,
            official_case,
            local_vertices,
            local_triangles,
            official_vertices,
            official_triangles,
            runtime,
            class_id,
            inverted,
        ))
    summary = oracle_compare.summarize(results)
    return summary


def write_markdown(report: Dict[str, object]) -> None:
    regular_report = report["regular"]  # type: ignore[index]
    transition_report = report["transition"]  # type: ignore[index]
    lines = [
        "# M24 Exact Topology Candidate",
        "",
        f"Status: `{report['status']}`",
        "",
        "The candidate keeps the clean-room boundary derivation and selects "
        "from independently enumerated triangulations using compact "
        "oracle-calibrated option indexes.",
        "",
        f"- Regular oriented topology: "
        f"`{regular_report['matches']['oriented_topology']}/256`",  # type: ignore[index]
        f"- Transition oriented topology: "
        f"`{transition_report['matches']['oriented_topology']}/512`",  # type: ignore[index]
        f"- Exact topology identity: "
        f"`{report['decisions']['exact_topology_identity']}`",  # type: ignore[index]
        f"- Exact replacement ready: "
        f"`{report['decisions']['exact_replacement_ready']}`",  # type: ignore[index]
        "",
        "The exact selection-bearing rules and tables are MIT. Generator code "
        "and this aggregate report remain 0BSD.",
        "",
    ]
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    oracle_path = oracle_compare.discover_oracle(None)
    origin = oracle_compare.git_value(
        oracle_path.parent,
        "remote",
        "get-url",
        "origin",
    )
    commit = oracle_compare.git_value(
        oracle_path.parent,
        "rev-parse",
        "HEAD",
    )
    if (
        origin != oracle_compare.EXPECTED_ORIGIN
        or commit != oracle_compare.EXPECTED_COMMIT
    ):
        raise RuntimeError(
            f"unexpected oracle provenance: {origin} {commit}"
        )
    oracle = oracle_compare.parse_oracle(oracle_path)
    rules = derive_rules(oracle_path, oracle)
    regular_source = {"cases": regular_cases(rules)}
    transition_source = {"cases": transition_cases(rules)}
    tables: Dict[str, object] = {
        "schema": "boqsc.transvoxel.m24.exact_topology_tables.v1",
        "generator_code_license": "0BSD",
        "license": "MIT",
        "license_file": "LICENSES/MIT.txt",
        "copyright": "Copyright (c) 2009 Eric Lengyel",
        "generated_candidate_license_status": "MIT_EXACT_COMPATIBILITY_DATA",
        "status": "M24_MIT_EXACT_TOPOLOGY_CANDIDATE",
        "meaning": (
            "Direct per-case runtime tables generated from clean-room boundary "
            "loops and compact oracle-calibrated triangulation selections."
        ),
        "rules_sha256": canonical_sha(rules),
        "regular": export_transvoxel.build_table(
            regular_source,
            "m24_regular",
        ),
        "transition": export_transvoxel.build_table(
            transition_source,
            "m24_transition",
        ),
    }
    tables["sha256_without_this_field"] = canonical_sha(tables)

    regular_report = compare_section(
        oracle,
        tables["regular"],  # type: ignore[arg-type]
        "regular",
    )
    transition_report = compare_section(
        oracle,
        tables["transition"],  # type: ignore[arg-type]
        "transition",
    )
    exact_topology = (
        regular_report["matches"]["oriented_topology"] == 256  # type: ignore[index]
        and transition_report["matches"]["oriented_topology"] == 512  # type: ignore[index]
    )
    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.m24.exact_topology_report.v1",
        "report_license": "0BSD",
        "aggregate_only": True,
        "contains_exact_arrays": False,
        "exact_candidate_data_license": "MIT",
        "status": (
            "PASS_M24_EXACT_REGULAR_TRANSITION_TOPOLOGY"
            if exact_topology
            else "FAIL_M24_EXACT_TOPOLOGY"
        ),
        "oracle": {
            "origin": origin,
            "commit": commit,
            "sha256": sha256_file(oracle_path),
            "verified": True,
        },
        "rules": {
            "path": "research/official_topology/m24/topology_rules.json",
            "sha256": canonical_sha(rules),
            "regular_rule_count": len(
                rules["regular"]["rules"]  # type: ignore[index]
            ),
            "transition_class_rule_count": len(
                rules["transition"]["rules"]  # type: ignore[index]
            ),
        },
        "regular": regular_report,
        "transition": transition_report,
        "decisions": {
            "exact_topology_identity": exact_topology,
            "official_vertex_ordering_ready": False,
            "official_reuse_encoding_ready": False,
            "official_class_table_layout_ready": False,
            "exact_0bsd_provenance_cleared": False,
            "unchanged_consumer_integration_ready": False,
            "exact_replacement_ready": False,
        },
        "next_milestone": {
            "id": "M25_EXACT_VERTEX_ENCODING_AND_TABLE_LAYOUT",
            "objective": (
                "Derive official-compatible vertex order/reuse encodings and "
                "class/table layout, then expose an unchanged-consumer surface."
            ),
        },
    }

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RULES_PATH.write_text(
        json.dumps(rules, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    TABLES_PATH.write_text(
        json.dumps(tables, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    header = export_transvoxel.emit_h(tables)
    header = header.replace(
        "/* SPDX-License-Identifier: 0BSD\n",
        (
            "/* SPDX-License-Identifier: MIT\n"
            " * Copyright (c) 2009 Eric Lengyel\n"
            " * Exact compatibility data. See LICENSES/MIT.txt.\n"
        ),
    ).replace(
        "BOQSC_TRANSVOXEL_TABLES_H",
        "BOQSC_M24_EXACT_TOPOLOGY_TABLES_H",
    ).replace(
        "Generated by tools/export_transvoxel.py.",
        "Generated by M24 exact-topology research.",
    ).replace(
        "Default transition source: clean-room M4 published-topology behavior.",
        (
            "Source: clean-room boundary loops with oracle-calibrated "
            "triangulation indexes."
        ),
    ).replace(
        (
            "Not copied from, and not byte-compatible with, Eric Lengyel's "
            "MIT Transvoxel.cpp."
        ),
        "Exact compatibility data licensed MIT; see LICENSES/MIT.txt.",
    )
    HEADER_PATH.write_text(header, encoding="utf-8")
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("M24 topology candidate:", report["status"])
    print(
        "regular oriented topology:",
        regular_report["matches"]["oriented_topology"],  # type: ignore[index]
        "/ 256",
    )
    print(
        "transition oriented topology:",
        transition_report["matches"]["oriented_topology"],  # type: ignore[index]
        "/ 512",
    )
    print(TABLES_PATH)
    return 0 if exact_topology else 1


if __name__ == "__main__":
    raise SystemExit(main())
