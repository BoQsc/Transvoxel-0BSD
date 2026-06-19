#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate M3/M4 against the published transition topology rules.

This proves behavioral topology: public face contours, the D4/inversion class
construction, and valid minimal genus-zero fillings. It intentionally does not
claim identical official interior diagonals, class numbers, vertex codes, or
table bytes.
"""
from __future__ import annotations

from collections import defaultdict
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "published_transition_topology_report.json"
MD = ROOT / "validation" / "published_transition_topology_report.md"
M3_DIR = ROOT / "research" / "official_topology" / "m3"

sys.path.insert(0, str(M3_DIR))
import m3_core as m3  # noqa: E402

Vertex = Tuple[int, int]
MeshEdge = Tuple[Vertex, Vertex]
Triangle = Tuple[Vertex, Vertex, Vertex]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def edge(a: Vertex, b: Vertex) -> MeshEdge:
    return (a, b) if a < b else (b, a)


def serialized_vertex(value: Sequence[int]) -> Vertex:
    return (int(value[0]), int(value[1]))


def expected_square_segments(
    case_index: int,
    square: Sequence[int],
) -> Set[Tuple[Vertex, Vertex]]:
    crossings: List[Vertex] = []
    for index, sample_id in enumerate(square):
        next_sample = square[(index + 1) % 4]
        if (
            m3.sample_sign(case_index, sample_id)
            != m3.sample_sign(case_index, next_sample)
        ):
            crossings.append(m3.edge_key(sample_id, next_sample))
    if not crossings:
        return set()
    if len(crossings) == 2:
        return {m3.segment_key(crossings[0], crossings[1])}
    if len(crossings) != 4:
        raise AssertionError("square must have zero, two, or four crossings")
    result = set()
    for index, sample_id in enumerate(square):
        if not m3.sample_sign(case_index, sample_id):
            continue
        previous_edge = m3.edge_key(square[(index - 1) % 4], sample_id)
        next_edge = m3.edge_key(sample_id, square[(index + 1) % 4])
        result.add(m3.segment_key(previous_edge, next_edge))
    return result


def expected_lateral_segments(
    case_index: int,
    full_samples: Sequence[int],
    half_samples: Sequence[int],
) -> Tuple[Set[Tuple[Vertex, Vertex]], str]:
    a, b, c = full_samples
    half_a, half_c = half_samples
    sign_a = m3.sample_sign(case_index, a)
    sign_b = m3.sample_sign(case_index, b)
    sign_c = m3.sample_sign(case_index, c)
    if sign_a == sign_b == sign_c:
        return set(), "uniform"
    if sign_a == sign_c and sign_a != sign_b:
        return {
            m3.segment_key(
                m3.edge_key(a, b),
                m3.edge_key(b, c),
            )
        }, "alternating_full_face_edge"
    full_crossing = (
        m3.edge_key(a, b)
        if sign_a != sign_b
        else m3.edge_key(b, c)
    )
    return {
        m3.segment_key(
            full_crossing,
            m3.edge_key(half_a, half_c),
        )
    }, "full_to_half"


def segments_from_json(values: Sequence[Sequence[Sequence[int]]]) -> Set[
    Tuple[Vertex, Vertex]
]:
    result = set()
    for value in values:
        a = serialized_vertex(value[0])
        b = serialized_vertex(value[1])
        result.add(m3.segment_key(a, b))
    return result


def topology_metrics(case: Dict[str, Any]) -> Dict[str, int]:
    triangles: List[Triangle] = [
        tuple(serialized_vertex(vertex) for vertex in triangle)
        for triangle in case["triangles"]
    ]  # type: ignore[assignment]
    vertices = {vertex for triangle in triangles for vertex in triangle}
    uses: Dict[MeshEdge, List[int]] = defaultdict(list)
    adjacency: Dict[int, Set[int]] = defaultdict(set)
    for triangle_id, triangle in enumerate(triangles):
        for a, b in (
            (triangle[0], triangle[1]),
            (triangle[1], triangle[2]),
            (triangle[2], triangle[0]),
        ):
            uses[edge(a, b)].append(triangle_id)
    for edge_uses in uses.values():
        if len(edge_uses) == 2:
            a, b = edge_uses
            adjacency[a].add(b)
            adjacency[b].add(a)

    components = 0
    seen = set()
    for start in range(len(triangles)):
        if start in seen:
            continue
        components += 1
        seen.add(start)
        pending = [start]
        while pending:
            triangle_id = pending.pop()
            for neighbor in adjacency[triangle_id]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append(neighbor)

    boundary_edges = {
        mesh_edge for mesh_edge, edge_uses in uses.items()
        if len(edge_uses) == 1
    }
    loop_count = len(case["loops"])
    vertex_count = len(vertices)
    edge_count = len(uses)
    triangle_count = len(triangles)
    euler = vertex_count - edge_count + triangle_count
    return {
        "vertices": vertex_count,
        "edges": edge_count,
        "triangles": triangle_count,
        "components": components,
        "boundary_loops": loop_count,
        "boundary_edges": len(boundary_edges),
        "euler_characteristic": euler,
        "expected_euler_genus_zero": 2 * components - loop_count,
        "expected_minimal_boundary_only_triangles": (
            vertex_count - 4 * components + 2 * loop_count
        ),
        "nonmanifold_edges": sum(
            1 for edge_uses in uses.values() if len(edge_uses) > 2
        ),
    }


def validate_class_partition(
    partition: Dict[str, Any],
) -> Tuple[Dict[str, int], List[str]]:
    failures: List[str] = []
    metrics = {
        "classes": len(partition["classes"]),
        "member_cases": 0,
        "base_with_inversion": 0,
        "base_without_inversion": 0,
        "inverse_full_ambiguity": 0,
        "inverse_half_ambiguity": 0,
        "membership_failures": 0,
        "inversion_rule_failures": 0,
    }
    seen = set()
    classes = partition["classes"]
    for record in classes:
        class_id = int(record["research_class_id"])
        representative = int(record["representative_case"])
        kind = str(record["kind"])
        members = {int(value) for value in record["cases"]}
        orbit = set(m3.d4_orbit(representative))
        metrics["member_cases"] += len(members)
        overlap = seen & members
        if overlap:
            failures.append(f"class {class_id}: overlapping cases")
            metrics["membership_failures"] += len(overlap)
        seen.update(members)

        if kind == "base_with_inversion":
            metrics["base_with_inversion"] += 1
            expected = orbit | {case ^ m3.CASE_MASK for case in orbit}
            flags = m3.ambiguity_flags(representative)
            if flags["has_any_ambiguity"]:
                failures.append(
                    f"class {class_id}: inversion included despite ambiguity"
                )
                metrics["inversion_rule_failures"] += 1
        elif kind == "base_without_inversion":
            metrics["base_without_inversion"] += 1
            expected = orbit
            flags = m3.ambiguity_flags(representative)
            if not flags["has_any_ambiguity"]:
                failures.append(
                    f"class {class_id}: inversion split without ambiguity"
                )
                metrics["inversion_rule_failures"] += 1
            inverse_id = record.get("inverse_research_class_id")
            if inverse_id is None:
                failures.append(f"class {class_id}: missing inverse class")
                metrics["inversion_rule_failures"] += 1
        elif kind.startswith("inverse_split_"):
            base_id = int(record["source_base_research_class_id"])
            base = classes[base_id]
            base_orbit = set(m3.d4_orbit(int(base["representative_case"])))
            expected = {case ^ m3.CASE_MASK for case in base_orbit}
            if kind == "inverse_split_full_resolution_ambiguity":
                metrics["inverse_full_ambiguity"] += 1
            else:
                metrics["inverse_half_ambiguity"] += 1
        else:
            expected = set()
            failures.append(f"class {class_id}: unknown kind {kind}")
            metrics["membership_failures"] += 1
        if members != expected:
            failures.append(f"class {class_id}: D4/inversion membership mismatch")
            metrics["membership_failures"] += 1

    if seen != set(range(512)):
        failures.append("class partition does not cover exactly 512 cases")
        metrics["membership_failures"] += 1
    return metrics, failures


def write_markdown(report: Dict[str, Any]) -> None:
    metrics = report["metrics"]
    lines = [
        "# Published Transition Topology Validation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Published transition topology behavior: **{report['published_transition_topology_behavior']}**",
        "",
        "## Exhaustive coverage",
        "",
        f"- Cases: `{metrics['cases']}`",
        f"- Research classes: `{metrics['class_partition']['classes']}`",
        f"- Full-face quadrant checks: `{metrics['full_face_quadrant_checks']}`",
        f"- Half-face checks: `{metrics['half_face_checks']}`",
        f"- Lateral-face checks: `{metrics['lateral_face_checks']}`",
        f"- Boundary loops: `{metrics['boundary_loops']}`",
        f"- Surface components: `{metrics['surface_components']}`",
        f"- Candidate triangles: `{metrics['triangles']}`",
        f"- Failures: `{len(report['failures'])}`",
        "",
        "This proves the published topology behavior required for a functional transition implementation. It does not claim identical official interior diagonals, class numbers, vertex/cache codes, or table bytes.",
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    partition = read_json(M3_DIR / "class_partition.json")
    boundary = read_json(M3_DIR / "boundary_loops.json")
    candidates = read_json(M3_DIR / "candidate_triangulations.json")
    m4_validation = read_json(
        ROOT
        / "research"
        / "official_topology"
        / "m4"
        / "runtime_table_validation.json"
    )
    reference = read_json(
        ROOT / "validation" / "reference_convention_report.json"
    )

    failures: List[str] = []
    class_metrics, class_failures = validate_class_partition(partition)
    failures.extend(class_failures)
    boundary_cases = {
        int(case["case"]): case for case in boundary["cases"]
    }
    candidate_cases = {
        int(case["case"]): case for case in candidates["cases"]
    }
    metrics: Dict[str, Any] = {
        "cases": 512,
        "full_face_quadrant_checks": 0,
        "half_face_checks": 0,
        "lateral_face_checks": 0,
        "lateral_configurations": {
            "uniform": 0,
            "full_to_half": 0,
            "alternating_full_face_edge": 0,
        },
        "boundary_segments": 0,
        "boundary_loops": 0,
        "surface_components": 0,
        "triangles": 0,
        "topology_case_failures": 0,
        "class_partition": class_metrics,
    }

    for case_index in range(512):
        boundary_case = boundary_cases[case_index]
        candidate = candidate_cases[case_index]
        by_face = boundary_case["segments_by_face"]

        for name, square in m3.FULL_QUADRANTS:
            expected = expected_square_segments(case_index, square)
            actual = segments_from_json(by_face[name])
            if actual != expected:
                failures.append(
                    f"case {case_index} {name}: full-face contour mismatch"
                )
                metrics["topology_case_failures"] += 1
            metrics["full_face_quadrant_checks"] += 1

        expected_half = expected_square_segments(
            case_index,
            m3.HALF_FACE[1],
        )
        actual_half = segments_from_json(by_face[m3.HALF_FACE[0]])
        if actual_half != expected_half:
            failures.append(f"case {case_index}: half-face contour mismatch")
            metrics["topology_case_failures"] += 1
        metrics["half_face_checks"] += 1

        for name, full_samples, half_samples in m3.LATERAL_FACES:
            expected, category = expected_lateral_segments(
                case_index,
                full_samples,
                half_samples,
            )
            actual = segments_from_json(by_face[name])
            if actual != expected:
                failures.append(
                    f"case {case_index} {name}: lateral contour mismatch"
                )
                metrics["topology_case_failures"] += 1
            metrics["lateral_configurations"][category] += 1
            metrics["lateral_face_checks"] += 1

        topology = topology_metrics(candidate)
        metrics["boundary_segments"] += len(candidate["segments"])
        metrics["boundary_loops"] += topology["boundary_loops"]
        metrics["surface_components"] += topology["components"]
        metrics["triangles"] += topology["triangles"]
        expected_boundary = segments_from_json(candidate["segments"])
        triangle_boundary: Set[MeshEdge] = set()
        triangle_uses: Dict[MeshEdge, int] = defaultdict(int)
        for triangle in candidate["triangles"]:
            vertices = [serialized_vertex(value) for value in triangle]
            for a, b in (
                (vertices[0], vertices[1]),
                (vertices[1], vertices[2]),
                (vertices[2], vertices[0]),
            ):
                triangle_uses[edge(a, b)] += 1
        triangle_boundary = {
            mesh_edge
            for mesh_edge, count in triangle_uses.items()
            if count == 1
        }
        topology_ok = (
            candidate["status"] == "PASS"
            and candidate["validation"]["status"] == "PASS"
            and topology["nonmanifold_edges"] == 0
            and triangle_boundary == expected_boundary
            and topology["euler_characteristic"]
            == topology["expected_euler_genus_zero"]
            and topology["triangles"]
            == topology["expected_minimal_boundary_only_triangles"]
        )
        if not topology_ok:
            failures.append(
                f"case {case_index}: invalid minimal genus-zero filling"
            )
            metrics["topology_case_failures"] += 1

    checks = {
        "published_reference_convention_is_proven": (
            reference.get("reference_equivalence_status") == "PROVEN"
        ),
        "class_partition_is_51_plus_18_plus_4": (
            partition.get("base_class_count") == 51
            and partition.get("full_resolution_inverse_split_count") == 18
            and partition.get("half_resolution_only_inverse_split_count") == 4
            and partition.get("research_class_count") == 73
        ),
        "all_512_cases_have_exact_d4_inversion_membership": (
            class_metrics["membership_failures"] == 0
            and class_metrics["inversion_rule_failures"] == 0
            and class_metrics["member_cases"] == 512
        ),
        "all_published_full_and_half_face_contours_match": (
            metrics["full_face_quadrant_checks"] == 2048
            and metrics["half_face_checks"] == 512
            and metrics["topology_case_failures"] == 0
        ),
        "all_published_lateral_face_configurations_match": (
            metrics["lateral_face_checks"] == 2048
            and all(
                value > 0
                for value in metrics["lateral_configurations"].values()
            )
            and metrics["topology_case_failures"] == 0
        ),
        "all_boundary_graphs_are_closed_degree_two_loops": (
            boundary.get("failure_count") == 0
            and boundary.get("case_count") == 512
        ),
        "all_cases_have_minimal_genus_zero_candidate_surfaces": (
            candidates.get("failure_count") == 0
            and candidates.get("class_topology_signature_failure_count") == 0
            and metrics["topology_case_failures"] == 0
        ),
        "m4_runtime_preserves_m3_topology_and_winding": (
            m4_validation.get("case_topology_failure_count") == 0
            and m4_validation.get("case_winding_failure_count") == 0
            and m4_validation.get("transform_failure_count") == 0
        ),
    }
    ok = all(checks.values()) and not failures
    report = {
        "schema": "boqsc.transvoxel.published_transition_topology.v1",
        "status": (
            "PASS_PUBLISHED_TRANSITION_TOPOLOGY_BEHAVIOR"
            if ok
            else "FAIL_PUBLISHED_TRANSITION_TOPOLOGY"
        ),
        "published_transition_topology_behavior": (
            "PROVEN" if ok else "NOT_PROVEN"
        ),
        "checks": checks,
        "metrics": metrics,
        "failures": failures[:100],
        "source_reference": {
            "title": "Voxel-Based Terrain for Real-Time Virtual Simulations",
            "author": "Eric Lengyel",
            "url": "https://transvoxel.org/Lengyel-VoxelTerrain.pdf",
            "relevant_public_rules": [
                "Section 4.3: D4 action on nine coplanar samples",
                "Section 4.3: inversion only when full and half faces are unambiguous",
                "Figure 3.5: preferred-polarity full/half face contours",
                "Figure 4.10: four nontrivial lateral configurations modulo vertical flip",
                "Section 4.3: coincident lateral faces require matching endpoints and opposite winding",
            ],
        },
        "claim_boundary": {
            "proven": (
                "Published transition topology behavior for all 512 cases: "
                "face contours, class symmetry/inversion rules, closed "
                "boundaries, and valid minimal genus-zero fillings."
            ),
            "not_proven": [
                "identical official interior triangle diagonals",
                "official numeric class IDs",
                "official vertex/cache encoding",
                "Transvoxel.cpp table bytes",
            ],
        },
        "no_copy_rule": (
            "Uses dissertation prose/figures and clean-room derivation only; "
            "no official lookup-table arrays or array values are read."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("published transition topology:", report["status"])
    print(
        "cases=512 classes=",
        class_metrics["classes"],
        "face_checks=",
        (
            metrics["full_face_quadrant_checks"]
            + metrics["half_face_checks"]
            + metrics["lateral_face_checks"]
        ),
        "triangles=",
        metrics["triangles"],
        "failures=",
        len(failures),
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
