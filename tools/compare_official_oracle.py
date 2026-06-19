#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compare the 0BSD runtime tables with an external official MIT oracle.

The oracle file is never copied into this repository. This tool reads an
explicitly supplied Eric Lengyel Transvoxel.cpp, compares all regular and
transition cases, and writes only aggregate results plus per-case mismatch
categories. It does not emit oracle table values.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
TABLES_PATH = ROOT / "generated" / "transvoxel_tables.json"
REPORT_JSON = ROOT / "validation" / "official_oracle_comparison_report.json"
REPORT_MD = ROOT / "validation" / "official_oracle_comparison_report.md"

EXPECTED_ORIGIN = "https://github.com/EricLengyel/Transvoxel.git"
EXPECTED_COMMIT = "51a494f03c5b024cd153b596bcc7152eb3cc93a6"

Edge = Tuple[int, int]
EdgeTriangle = Tuple[Edge, Edge, Edge]

# Local row-major transition samples 0..8 map to the official case-bit order.
LOCAL_TO_OFFICIAL_CASE_BIT = (0, 1, 2, 7, 8, 3, 6, 5, 4)

# Official Figure 4.16 endpoint ids are already the row-major sampling order
# used by this project. Only the case-index bit order differs.
OFFICIAL_TO_LOCAL_TRANSITION_SAMPLE = tuple(range(13))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_sha(data: object) -> str:
    encoded = json.dumps(
        data, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalize_edge(a: int, b: int) -> Edge:
    if a == b:
        raise ValueError(f"degenerate edge ({a}, {b})")
    return (a, b) if a < b else (b, a)


def strip_line_comments(text: str) -> str:
    return re.sub(r"//[^\n]*", "", text)


def initializer_body(text: str, declaration_pattern: str) -> str:
    match = re.search(declaration_pattern, text)
    if not match:
        raise ValueError(f"declaration not found: {declaration_pattern}")
    start = text.find("{", match.end())
    if start < 0:
        raise ValueError(f"initializer not found: {declaration_pattern}")
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index]
    raise ValueError(f"unterminated initializer: {declaration_pattern}")


def top_level_records(body: str) -> List[str]:
    records: List[str] = []
    depth = 0
    start = -1
    for index, char in enumerate(body):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced initializer braces")
            if depth == 0 and start >= 0:
                records.append(body[start:index + 1])
                start = -1
    if depth != 0:
        raise ValueError("unbalanced initializer braces")
    return records


def ints(text: str) -> List[int]:
    return [
        int(token, 0)
        for token in re.findall(r"0[xX][0-9A-Fa-f]+|\b\d+\b", text)
    ]


def parse_oracle(path: Path) -> Dict[str, object]:
    text = strip_line_comments(path.read_text(encoding="utf-8"))

    regular_classes = ints(initializer_body(
        text, r"regularCellClass\s*\[\s*256\s*\]"
    ))
    regular_data_records = top_level_records(initializer_body(
        text, r"regularCellData\s*\[\s*16\s*\]"
    ))
    regular_vertex_records = top_level_records(initializer_body(
        text, r"regularVertexData\s*\[\s*256\s*\]\s*\[\s*12\s*\]"
    ))
    transition_classes = ints(initializer_body(
        text, r"transitionCellClass\s*\[\s*512\s*\]"
    ))
    transition_data_records = top_level_records(initializer_body(
        text, r"transitionCellData\s*\[\s*56\s*\]"
    ))
    transition_corner_data = ints(initializer_body(
        text, r"transitionCornerData\s*\[\s*13\s*\]"
    ))
    transition_vertex_records = top_level_records(initializer_body(
        text, r"transitionVertexData\s*\[\s*512\s*\]\s*\[\s*12\s*\]"
    ))

    regular_data = []
    for record in regular_data_records:
        values = ints(record)
        geometry = values[0]
        regular_data.append({
            "vertex_count": geometry >> 4,
            "triangle_count": geometry & 0x0F,
            "indices": values[1:],
        })

    transition_data = []
    for record in transition_data_records:
        values = ints(record)
        geometry = values[0]
        transition_data.append({
            "vertex_count": geometry >> 4,
            "triangle_count": geometry & 0x0F,
            "indices": values[1:],
        })

    parsed: Dict[str, object] = {
        "regular_classes": regular_classes,
        "regular_data": regular_data,
        "regular_vertices": [ints(record) for record in regular_vertex_records],
        "transition_classes": transition_classes,
        "transition_data": transition_data,
        "transition_corner_data": transition_corner_data,
        "transition_vertices": [
            ints(record) for record in transition_vertex_records
        ],
    }
    expected_lengths = {
        "regular_classes": 256,
        "regular_data": 16,
        "regular_vertices": 256,
        "transition_classes": 512,
        "transition_data": 56,
        "transition_corner_data": 13,
        "transition_vertices": 512,
    }
    for key, expected in expected_lengths.items():
        actual = len(parsed[key])  # type: ignore[arg-type]
        if actual != expected:
            raise ValueError(f"{key}: expected {expected}, got {actual}")
    return parsed


def git_value(repo: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return "UNKNOWN"
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"


def discover_oracle(explicit: str | None) -> Path:
    candidates: List[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env_path = os.environ.get("TRANSVOXEL_ORACLE_CPP")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path.home()
        / "Documents"
        / "Playground"
        / "transvoxel_godot"
        / "references"
        / "transvoxel_repo"
        / "Transvoxel.cpp",
        ROOT / "external" / "Transvoxel.cpp",
    ])
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.is_file():
            return resolved
    raise FileNotFoundError(
        "official Transvoxel.cpp oracle not found; pass --oracle or set "
        "TRANSVOXEL_ORACLE_CPP"
    )


def local_transition_to_official_case(case_index: int) -> int:
    result = 0
    for local_bit, official_bit in enumerate(LOCAL_TO_OFFICIAL_CASE_BIT):
        if case_index & (1 << local_bit):
            result |= 1 << official_bit
    return result


def decode_regular_edge(code: int) -> Edge:
    low = code & 0xFF
    return normalize_edge((low >> 4) & 0x0F, low & 0x0F)


def decode_transition_edge(code: int) -> Edge:
    low = code & 0xFF
    official_a = (low >> 4) & 0x0F
    official_b = low & 0x0F
    if official_a >= len(OFFICIAL_TO_LOCAL_TRANSITION_SAMPLE):
        raise ValueError(f"bad official transition endpoint {official_a}")
    if official_b >= len(OFFICIAL_TO_LOCAL_TRANSITION_SAMPLE):
        raise ValueError(f"bad official transition endpoint {official_b}")
    return normalize_edge(
        OFFICIAL_TO_LOCAL_TRANSITION_SAMPLE[official_a],
        OFFICIAL_TO_LOCAL_TRANSITION_SAMPLE[official_b],
    )


def case_from_export(
    section: Dict[str, object], case_index: int
) -> Tuple[List[Edge], List[Tuple[int, int, int]]]:
    case_class = section["case_class"]  # type: ignore[index]
    class_data = section["class_data"]  # type: ignore[index]
    vertex_refs = section["vertex_refs"]  # type: ignore[index]
    triangles = section["triangles"]  # type: ignore[index]
    class_index = int(case_class[case_index])  # type: ignore[index]
    data = class_data[class_index]  # type: ignore[index]
    vertex_offset = int(data["vertex_offset"])
    vertex_count = int(data["vertex_count"])
    triangle_offset = int(data["triangle_offset"])
    triangle_count = int(data["triangle_count"])
    vertices = [
        normalize_edge(int(value[0]), int(value[1]))
        for value in vertex_refs[  # type: ignore[index]
            vertex_offset:vertex_offset + vertex_count
        ]
    ]
    case_triangles = [
        (int(value[0]), int(value[1]), int(value[2]))
        for value in triangles[  # type: ignore[index]
            triangle_offset:triangle_offset + triangle_count
        ]
    ]
    return vertices, case_triangles


def edge_triangles(
    vertices: Sequence[Edge],
    triangles: Sequence[Tuple[int, int, int]],
) -> List[EdgeTriangle]:
    return [
        (vertices[a], vertices[b], vertices[c])
        for a, b, c in triangles
    ]


def unoriented_triangle_key(triangle: EdgeTriangle) -> Tuple[Edge, Edge, Edge]:
    return tuple(sorted(triangle))  # type: ignore[return-value]


def oriented_triangle_key(triangle: EdgeTriangle) -> EdgeTriangle:
    a, b, c = triangle
    return min((a, b, c), (b, c, a), (c, a, b))


def topology_hash(
    triangles: Iterable[EdgeTriangle], oriented: bool
) -> str:
    if oriented:
        normalized = sorted(oriented_triangle_key(tri) for tri in triangles)
    else:
        normalized = sorted(unoriented_triangle_key(tri) for tri in triangles)
    return canonical_json_sha(normalized)


def compare_case(
    local_case: int,
    official_case: int,
    local_vertices: List[Edge],
    local_indices: List[Tuple[int, int, int]],
    official_vertices: List[Edge],
    official_raw_indices: List[Tuple[int, int, int]],
    official_runtime_indices: List[Tuple[int, int, int]],
    official_class_id: int,
    official_inverted: bool,
) -> Dict[str, object]:
    local_edge_triangles = edge_triangles(local_vertices, local_indices)
    official_raw_triangles = edge_triangles(
        official_vertices, official_raw_indices
    )
    official_runtime_triangles = edge_triangles(
        official_vertices, official_runtime_indices
    )

    vertex_count_match = len(local_vertices) == len(official_vertices)
    triangle_count_match = len(local_indices) == len(official_raw_indices)
    vertex_edge_set_match = Counter(local_vertices) == Counter(official_vertices)
    vertex_order_match = local_vertices == official_vertices
    topology_unoriented_match = (
        Counter(map(unoriented_triangle_key, local_edge_triangles))
        == Counter(map(unoriented_triangle_key, official_raw_triangles))
    )
    topology_oriented_match = (
        Counter(map(oriented_triangle_key, local_edge_triangles))
        == Counter(map(oriented_triangle_key, official_runtime_triangles))
    )
    raw_index_order_match = (
        vertex_order_match and local_indices == official_raw_indices
    )
    runtime_index_order_match = (
        vertex_order_match and local_indices == official_runtime_indices
    )

    mismatches = []
    checks = {
        "vertex_count": vertex_count_match,
        "triangle_count": triangle_count_match,
        "vertex_edge_set": vertex_edge_set_match,
        "vertex_order": vertex_order_match,
        "unoriented_topology": topology_unoriented_match,
        "oriented_topology": topology_oriented_match,
        "raw_index_order": raw_index_order_match,
        "runtime_index_order": runtime_index_order_match,
    }
    for name, passed in checks.items():
        if not passed:
            mismatches.append(name)

    return {
        "local_case": local_case,
        "official_case": official_case,
        "official_class_id": official_class_id,
        "official_inverted": official_inverted,
        "local_vertex_count": len(local_vertices),
        "official_vertex_count": len(official_vertices),
        "local_triangle_count": len(local_indices),
        "official_triangle_count": len(official_raw_indices),
        "checks": checks,
        "mismatches": mismatches,
        "local_unoriented_topology_sha256": topology_hash(
            local_edge_triangles, oriented=False
        ),
        "official_unoriented_topology_sha256": topology_hash(
            official_raw_triangles, oriented=False
        ),
    }


def official_regular_case(
    oracle: Dict[str, object], case_index: int
) -> Tuple[List[Edge], List[Tuple[int, int, int]], int]:
    classes = oracle["regular_classes"]  # type: ignore[index]
    class_data = oracle["regular_data"]  # type: ignore[index]
    vertex_data = oracle["regular_vertices"]  # type: ignore[index]
    class_id = int(classes[case_index])  # type: ignore[index]
    data = class_data[class_id]  # type: ignore[index]
    vertex_count = int(data["vertex_count"])
    triangle_count = int(data["triangle_count"])
    vertices = [
        decode_regular_edge(int(code))
        for code in vertex_data[case_index][:vertex_count]  # type: ignore[index]
    ]
    flat = data["indices"][:triangle_count * 3]
    triangles = [
        (int(flat[i]), int(flat[i + 1]), int(flat[i + 2]))
        for i in range(0, len(flat), 3)
    ]
    return vertices, triangles, class_id


def official_transition_case(
    oracle: Dict[str, object], official_case: int
) -> Tuple[
    List[Edge],
    List[Tuple[int, int, int]],
    List[Tuple[int, int, int]],
    int,
    bool,
]:
    classes = oracle["transition_classes"]  # type: ignore[index]
    class_data = oracle["transition_data"]  # type: ignore[index]
    vertex_data = oracle["transition_vertices"]  # type: ignore[index]
    class_code = int(classes[official_case])  # type: ignore[index]
    class_id = class_code & 0x7F
    inverted = bool(class_code & 0x80)
    data = class_data[class_id]  # type: ignore[index]
    vertex_count = int(data["vertex_count"])
    triangle_count = int(data["triangle_count"])
    vertices = [
        decode_transition_edge(int(code))
        for code in vertex_data[official_case][:vertex_count]  # type: ignore[index]
    ]
    flat = data["indices"][:triangle_count * 3]
    raw = [
        (int(flat[i]), int(flat[i + 1]), int(flat[i + 2]))
        for i in range(0, len(flat), 3)
    ]
    # The official table contract says the high class bit reverses winding.
    runtime = [(c, b, a) for a, b, c in raw] if inverted else raw
    return vertices, raw, runtime, class_id, inverted


def summarize(cases: Sequence[Dict[str, object]]) -> Dict[str, object]:
    check_names = list(cases[0]["checks"]) if cases else []
    matches = {
        name: sum(
            1 for case in cases if bool(case["checks"][name])  # type: ignore[index]
        )
        for name in check_names
    }
    mismatch_histogram = Counter(
        mismatch
        for case in cases
        for mismatch in case["mismatches"]  # type: ignore[index]
    )
    return {
        "case_count": len(cases),
        "matches": matches,
        "mismatches": {
            name: len(cases) - count for name, count in matches.items()
        },
        "mismatch_category_histogram": dict(sorted(mismatch_histogram.items())),
        "all_unoriented_topology_match": (
            matches.get("unoriented_topology", 0) == len(cases)
        ),
        "all_oriented_topology_match": (
            matches.get("oriented_topology", 0) == len(cases)
        ),
        "all_literal_runtime_case_encoding_match": (
            matches.get("runtime_index_order", 0) == len(cases)
        ),
    }


def write_markdown(report: Dict[str, object]) -> None:
    regular = report["regular"]  # type: ignore[index]
    transition = report["transition"]  # type: ignore[index]
    lines = [
        "# M23 Official Oracle Comparison",
        "",
        f"Status: `{report['status']}`",
        "",
        "The external MIT file is used only as an isolated comparison oracle. "
        "No oracle arrays are emitted or packaged in the 0BSD repository.",
        "",
        "## Oracle",
        "",
        f"- Origin: `{report['oracle']['origin']}`",  # type: ignore[index]
        f"- Commit: `{report['oracle']['commit']}`",  # type: ignore[index]
        f"- SHA-256: `{report['oracle']['sha256']}`",  # type: ignore[index]
        "",
        "## Exhaustive results",
        "",
        f"- Regular cases compared: `{regular['case_count']}`",  # type: ignore[index]
        f"- Regular unoriented topology matches: "
        f"`{regular['matches']['unoriented_topology']}`",  # type: ignore[index]
        f"- Regular oriented topology matches: "
        f"`{regular['matches']['oriented_topology']}`",  # type: ignore[index]
        f"- Transition cases compared: `{transition['case_count']}`",  # type: ignore[index]
        f"- Transition unoriented topology matches: "
        f"`{transition['matches']['unoriented_topology']}`",  # type: ignore[index]
        f"- Transition oriented topology matches: "
        f"`{transition['matches']['oriented_topology']}`",  # type: ignore[index]
        "",
        "## Exact replacement decision",
        "",
        f"- Exact topology ready: `{report['decisions']['exact_topology_ready']}`",  # type: ignore[index]
        f"- Exact table layout ready: "
        f"`{report['decisions']['exact_table_layout_ready']}`",  # type: ignore[index]
        f"- Exact replacement ready: "
        f"`{report['decisions']['exact_replacement_ready']}`",  # type: ignore[index]
        "",
        "The next milestone must change the implementation, not the claim "
        "wording: converge regular and transition case topology on the oracle "
        "before starting unchanged-consumer integration tests.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", help="path to official MIT Transvoxel.cpp")
    args = parser.parse_args()

    oracle_path = discover_oracle(args.oracle)
    oracle_repo = oracle_path.parent
    origin = git_value(oracle_repo, "remote", "get-url", "origin")
    commit = git_value(oracle_repo, "rev-parse", "HEAD")
    oracle_verified = origin == EXPECTED_ORIGIN and commit == EXPECTED_COMMIT
    if not oracle_verified:
        raise RuntimeError(
            "oracle provenance mismatch: "
            f"origin={origin!r} commit={commit!r}"
        )

    oracle = parse_oracle(oracle_path)
    tables = json.loads(TABLES_PATH.read_text(encoding="utf-8"))

    regular_cases: List[Dict[str, object]] = []
    for case_index in range(256):
        local_vertices, local_triangles = case_from_export(
            tables["regular"], case_index
        )
        official_vertices, official_triangles, class_id = (
            official_regular_case(oracle, case_index)
        )
        regular_cases.append(compare_case(
            case_index,
            case_index,
            local_vertices,
            local_triangles,
            official_vertices,
            official_triangles,
            official_triangles,
            class_id,
            False,
        ))

    transition_cases: List[Dict[str, object]] = []
    for local_case in range(512):
        official_case = local_transition_to_official_case(local_case)
        local_vertices, local_triangles = case_from_export(
            tables["transition"], local_case
        )
        (
            official_vertices,
            official_raw,
            official_runtime,
            class_id,
            inverted,
        ) = official_transition_case(oracle, official_case)
        transition_cases.append(compare_case(
            local_case,
            official_case,
            local_vertices,
            local_triangles,
            official_vertices,
            official_raw,
            official_runtime,
            class_id,
            inverted,
        ))

    regular_summary = summarize(regular_cases)
    transition_summary = summarize(transition_cases)
    exact_topology_ready = bool(
        regular_summary["all_oriented_topology_match"]
        and transition_summary["all_oriented_topology_match"]
    )
    exact_table_layout_ready = False
    exact_replacement_ready = exact_topology_ready and exact_table_layout_ready
    comparison_complete = (
        regular_summary["case_count"] == 256
        and transition_summary["case_count"] == 512
    )
    status = (
        "PASS_M23_OFFICIAL_ORACLE_BASELINE_EXACT_REPLACEMENT_NOT_READY"
        if oracle_verified and comparison_complete and not exact_replacement_ready
        else "FAIL_M23_OFFICIAL_ORACLE_BASELINE"
    )

    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.m23.official_oracle_comparison.v1",
        "status": status,
        "meaning": (
            "All 256 regular and 512 transition cases were compared with the "
            "verified external official oracle. A passing M23 status means the "
            "baseline is complete and honest; it does not mean exact "
            "replacement compatibility has passed."
        ),
        "oracle": {
            "license": "MIT",
            "origin": origin,
            "commit": commit,
            "sha256": sha256_file(oracle_path),
            "verified": oracle_verified,
            "bundled_in_0bsd_repository": False,
            "arrays_emitted_by_report": False,
        },
        "local_tables": {
            "path": "generated/transvoxel_tables.json",
            "sha256": sha256_file(TABLES_PATH),
        },
        "comparison_contract": {
            "regular_case_count": 256,
            "transition_case_count": 512,
            "transition_case_mapping_local_to_official_bits": list(
                LOCAL_TO_OFFICIAL_CASE_BIT
            ),
            "transition_endpoint_mapping_official_to_local": list(
                OFFICIAL_TO_LOCAL_TRANSITION_SAMPLE
            ),
            "unoriented_topology": (
                "triangle order and winding ignored; sample-edge identity kept"
            ),
            "oriented_topology": (
                "triangle order ignored; cyclic rotations allowed; winding kept"
            ),
            "literal_runtime_case_encoding": (
                "ordered vertex edges and runtime triangle index order"
            ),
        },
        "regular": {
            **regular_summary,
            "cases": regular_cases,
        },
        "transition": {
            **transition_summary,
            "cases": transition_cases,
        },
        "decisions": {
            "oracle_baseline_complete": comparison_complete,
            "exact_topology_ready": exact_topology_ready,
            "exact_table_layout_ready": exact_table_layout_ready,
            "exact_replacement_ready": exact_replacement_ready,
            "real_unchanged_consumer_integration_ready": exact_replacement_ready,
        },
        "known_structural_blockers": [
            "0BSD regular export uses 256 direct classes; official table uses 16 classes",
            "0BSD transition export uses 512 direct classes; official table uses 56 classes plus inversion bit",
            "0BSD vertex references do not contain official reuse metadata",
            "0BSD repository does not yet provide a field-for-field compatible Transvoxel.cpp surface",
        ],
        "next_milestone": {
            "id": "M24_EXACT_TOPOLOGY_CONVERGENCE",
            "objective": (
                "Converge every regular and transition case on official "
                "edge-labeled oriented topology using isolated oracle "
                "pass/fail reports, then rerun M23."
            ),
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("M23 official oracle comparison:", status)
    print(
        "regular oriented topology:",
        regular_summary["matches"]["oriented_topology"],  # type: ignore[index]
        "/ 256",
    )
    print(
        "transition oriented topology:",
        transition_summary["matches"]["oriented_topology"],  # type: ignore[index]
        "/ 512",
    )
    print("exact replacement ready:", exact_replacement_ready)
    return 0 if status.startswith("PASS_M23_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
