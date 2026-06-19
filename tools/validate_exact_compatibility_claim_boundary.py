#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the M22 exact-compatibility claim boundary.

M21 makes the public C/C++ API functionally ready as a clean-room
Transvoxel.cpp replacement. M22 locks the stronger exact-compatibility claims
behind explicit evidence gates so product docs and reports cannot drift into
claiming official table layout, class IDs, vertex/reuse encoding, triangulation
identity, or byte identity before those gates pass.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
REPORT_MD = ROOT / "validation" / "exact_compatibility_claim_boundary_report.md"

READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
M21_REPORT = ROOT / "research" / "official_topology" / "m21" / "m21_report.json"
CONSUMER_REPORT = ROOT / "validation" / "consumer_compatibility_report.json"
TRANSVOXEL_TABLES = ROOT / "generated" / "transvoxel_tables.json"

EXPECTED_READINESS_STATUS = (
    "READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_"
    "EXACT_COMPATIBILITY_BLOCKED"
)
EXPECTED_EXACT_BLOCKERS = {
    "official_class_id_mapping",
    "official_vertex_encoding_equivalence",
    "official_triangle_triangulation_identity",
    "official_regular_table_identity",
    "official_transvoxel_cpp_byte_identity",
}

CLAIM_FILES = [
    "README.md",
    "README_CORE.txt",
    "docs/API.md",
    "docs/CORE_PACKAGE_CONTENTS.md",
    "docs/DROP_IN.md",
    "docs/KNOWN_LIMITS.md",
    "docs/M4_REPLACEMENT_READINESS.md",
    "docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md",
    "docs/WHAT_THIS_PROVES.md",
    "PROVENANCE.md",
    "SOURCES.md",
]

REQUIRED_PHRASES = {
    "README.md": [
        "Functional full replacement readiness: READY by M21 through public C/C++ API",
        "Official Transvoxel.cpp / 73-class table equivalence: NOT_PROVEN",
    ],
    "README_CORE.txt": [
        "functional Transvoxel.cpp replacement through public C/C++ API",
        "does not claim official 73-class table or byte identity",
    ],
    "docs/KNOWN_LIMITS.md": [
        "M21 makes the public C/C++ API ready as a functional clean-room Transvoxel.cpp replacement",
        "Byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp table file is not proven.",
    ],
    "docs/M4_REPLACEMENT_READINESS.md": [
        "functional full replacement is ready through the public C/C++",
        "exact table/encoding/byte compatibility remains separate",
    ],
    "docs/WHAT_THIS_PROVES.md": [
        "the default clean-room M4 transition table and C/C++ consumer contract pass when RUN_M21 is executed",
        "byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp",
    ],
    "docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md": [
        "Functional clean-room Transvoxel.cpp replacement through the public C/C++ API.",
        "Byte-for-byte Transvoxel.cpp table/file identity claim.",
        "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY",
    ],
    "PROVENANCE.md": [
        "The default transition table is the M21 clean-room M4 export.",
        "Exact official class numbering, reuse encoding, triangulation identity, and table bytes are not claimed.",
    ],
}

FORBIDDEN_PATTERNS: List[Tuple[str, str]] = [
    (
        r"Official Transvoxel\.cpp\s*/\s*73-class table equivalence:\s*PROVEN",
        "README-style official equivalence marked PROVEN",
    ),
    (
        r"official_transvoxel_equivalence:\s*PROVEN",
        "machine-readable official equivalence marked PROVEN",
    ),
    (
        r"exact_table_compatible_replacement_ready[\"`:\s]+true",
        "exact table-compatible replacement marked ready",
    ),
    (
        r"byte[- ]for[- ]byte identity[^.\n]*(PROVEN|READY|PASS)",
        "byte identity marked proven/ready/pass",
    ),
    (
        r"field[- ]for[- ]field compatibility[^.\n]*(PROVEN|READY|PASS)",
        "field-for-field compatibility marked proven/ready/pass",
    ),
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def add_error(errors: List[Dict[str, Any]], check: str, detail: str, path: str | None = None) -> None:
    item: Dict[str, Any] = {"check": check, "detail": detail}
    if path:
        item["path"] = path
    errors.append(item)


def validate_reports() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    readiness = read_json(READINESS)
    m21 = read_json(M21_REPORT)
    consumer = read_json(CONSUMER_REPORT)
    tables = read_json(TRANSVOXEL_TABLES)

    decisions = readiness.get("decisions", {})
    blockers = set(readiness.get("blocking_gate_ids", []))
    claim_boundary = readiness.get("claim_boundary", {})
    source_tables = tables.get("source_tables", {})
    transition = tables.get("transition", {})

    if readiness.get("status") != EXPECTED_READINESS_STATUS:
        add_error(
            errors,
            "readiness_status",
            f"expected {EXPECTED_READINESS_STATUS}, got {readiness.get('status')}",
            rel(READINESS),
        )
    if decisions.get("functional_full_replacement_ready") is not True:
        add_error(errors, "functional_ready", "functional replacement is not ready", rel(READINESS))
    if decisions.get("exact_table_compatible_replacement_ready") is not False:
        add_error(errors, "exact_not_ready", "exact compatibility must remain false", rel(READINESS))
    if blockers != EXPECTED_EXACT_BLOCKERS:
        add_error(
            errors,
            "exact_blockers",
            f"expected {sorted(EXPECTED_EXACT_BLOCKERS)}, got {sorted(blockers)}",
            rel(READINESS),
        )
    if claim_boundary.get("byte_identity_required_for_functional_replacement") is not False:
        add_error(errors, "byte_identity_functional", "byte identity should not be required for functional replacement", rel(READINESS))
    if claim_boundary.get("byte_identity_required_for_exact_table_identity_claim") is not True:
        add_error(errors, "byte_identity_exact", "byte identity must be required for exact table identity claims", rel(READINESS))
    if "Functional clean-room Transvoxel.cpp replacement" not in str(claim_boundary.get("allowed_now", "")):
        add_error(errors, "allowed_claim", "functional replacement allowance is missing", rel(READINESS))
    if "Exact official Transvoxel.cpp" not in str(claim_boundary.get("not_allowed_now", "")):
        add_error(errors, "forbidden_claim", "exact official non-claim is missing", rel(READINESS))

    if m21.get("status") != "PASS_M21_DEFAULT_M4_FUNCTIONAL_CONSUMER_COMPATIBILITY":
        add_error(errors, "m21_status", f"M21 did not pass: {m21.get('status')}", rel(M21_REPORT))
    if m21.get("functional_transvoxel_cpp_replacement") != "PROVEN":
        add_error(errors, "m21_functional", "M21 functional replacement is not PROVEN", rel(M21_REPORT))
    if m21.get("exact_table_compatible_replacement") != "NOT_PROVEN":
        add_error(errors, "m21_exact", "M21 exact compatibility must be NOT_PROVEN", rel(M21_REPORT))

    if consumer.get("status") != "PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY":
        add_error(errors, "consumer_status", f"consumer contract did not pass: {consumer.get('status')}", rel(CONSUMER_REPORT))
    if consumer.get("functional_transvoxel_cpp_consumer_compatibility") != "PROVEN":
        add_error(errors, "consumer_functional", "consumer compatibility is not PROVEN", rel(CONSUMER_REPORT))
    if consumer.get("exact_table_layout_compatibility") is not False:
        add_error(errors, "consumer_exact_layout", "consumer exact layout compatibility must be false", rel(CONSUMER_REPORT))

    if source_tables.get("transition_source") != "generated/official_topology_candidate_tables.json":
        add_error(errors, "transition_source", "default transition source is not clean-room M4", rel(TRANSVOXEL_TABLES))
    if "no official 73-class packed layout" not in str(tables.get("compression", "")):
        add_error(errors, "compression_boundary", "table export does not declare no official 73-class packed layout", rel(TRANSVOXEL_TABLES))
    if int(transition.get("case_count", 0)) != 512 or int(transition.get("class_count", 0)) != 512:
        add_error(errors, "transition_layout", "default transition export must be direct 512-case layout", rel(TRANSVOXEL_TABLES))
    if len(transition.get("vertex_refs", [])) != 4096 or len(transition.get("triangles", [])) != 2640:
        add_error(errors, "transition_totals", "default transition totals are not M4 4096/2640", rel(TRANSVOXEL_TABLES))
    if int(transition.get("max_vertex_count", 0)) != 12 or int(transition.get("max_triangle_count", 0)) != 12:
        add_error(errors, "transition_maxima", "default transition maxima are not 12/12", rel(TRANSVOXEL_TABLES))

    evidence = {
        "readiness_status": readiness.get("status"),
        "decisions": decisions,
        "blocking_gate_ids": sorted(blockers),
        "claim_boundary": claim_boundary,
        "m21_status": m21.get("status"),
        "consumer_status": consumer.get("status"),
        "transition_source": source_tables.get("transition_source"),
        "transition_case_count": transition.get("case_count"),
        "transition_class_count": transition.get("class_count"),
        "transition_vertex_refs": len(transition.get("vertex_refs", [])),
        "transition_triangles": len(transition.get("triangles", [])),
        "transition_max_vertices": transition.get("max_vertex_count"),
        "transition_max_triangles": transition.get("max_triangle_count"),
    }
    return errors, evidence


def validate_text_claims() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    scanned: Dict[str, Any] = {}

    for rel_path in CLAIM_FILES:
        path = ROOT / rel_path
        if not path.exists():
            add_error(errors, "claim_file_exists", "missing claim-boundary file", rel_path)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        scanned[rel_path] = {"bytes": len(text.encode("utf-8"))}
        for phrase in REQUIRED_PHRASES.get(rel_path, []):
            if phrase not in text:
                add_error(errors, "required_phrase", f"missing phrase: {phrase}", rel_path)
        for pattern, reason in FORBIDDEN_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                # Allow negative uses such as "not proven" or "does not prove" on
                # the same line; M22 forbids positive exact-compatibility claims.
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(text)
                line = text[line_start:line_end]
                lowered = line.lower()
                if "not_proven" in lowered or "not proven" in lowered or "does not" in lowered or "not claim" in lowered or "not claimed" in lowered:
                    continue
                add_error(errors, "forbidden_exact_claim", f"{reason}: {line.strip()}", rel_path)

    return errors, scanned


def write_markdown(report: Dict[str, Any]) -> None:
    lines = [
        "# M22 Exact Compatibility Claim Boundary",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Allowed public claim",
        "",
        report["claim_contract"]["allowed_now"],
        "",
        "## Not allowed without future exact evidence",
        "",
    ]
    for item in report["claim_contract"]["not_allowed_now"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Evidence",
        "",
        f"- Readiness: `{report['evidence'].get('readiness_status')}`",
        f"- M21: `{report['evidence'].get('m21_status')}`",
        f"- Consumer contract: `{report['evidence'].get('consumer_status')}`",
        f"- Default transition source: `{report['evidence'].get('transition_source')}`",
        f"- Default transition totals: `{report['evidence'].get('transition_vertex_refs')}` vertex refs / `{report['evidence'].get('transition_triangles')}` triangles",
        "",
    ])
    if report["errors"]:
        lines.extend(["## Errors", ""])
        for err in report["errors"]:
            path = f" ({err.get('path')})" if err.get("path") else ""
            lines.append(f"- `{err['check']}`{path}: {err['detail']}")
        lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report_errors: List[Dict[str, Any]] = []
    evidence: Dict[str, Any] = {}
    try:
        report_errors, evidence = validate_reports()
    except Exception as exc:
        add_error(report_errors, "load_reports", repr(exc))

    text_errors, scanned = validate_text_claims()
    errors = [*report_errors, *text_errors]
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m22.exact_compatibility_claim_boundary.v1",
        "status": "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY" if not errors else "FAIL_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY",
        "meaning": (
            "Functional clean-room replacement is allowed through the public "
            "C/C++ API. Exact official Transvoxel.cpp table layout, 73-class "
            "IDs, vertex/reuse encoding, triangulation identity, and byte "
            "identity remain explicitly unclaimed until their gates pass."
        ),
        "claim_contract": {
            "allowed_now": (
                "Functional clean-room Transvoxel.cpp replacement through the "
                "public C/C++ API: default regular and transition builders use "
                "clean-room published behavior; C and C++ consumers can "
                "compile/link; callback customization is retained."
            ),
            "not_allowed_now": [
                "Exact official Transvoxel.cpp table layout claim.",
                "Official 73-class ID compatibility claim.",
                "Official vertex/reuse encoding compatibility claim.",
                "Exact official transition triangulation identity claim.",
                "Exact official regular table identity claim.",
                "Byte-for-byte Transvoxel.cpp table/file identity claim.",
            ],
            "byte_identity_required_for_functional_replacement": False,
            "byte_identity_required_for_exact_table_identity_claim": True,
            "official_arrays_allowed_as_generator_inputs": False,
        },
        "evidence": evidence,
        "scanned_claim_files": scanned,
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report)
    print("exact compatibility claim boundary:", report["status"])
    if errors:
        for err in errors[:20]:
            print("ERROR", err.get("path", ""), err["check"], err["detail"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
