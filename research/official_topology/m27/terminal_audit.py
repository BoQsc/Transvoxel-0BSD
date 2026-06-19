#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Make the terminal M27 exact-0BSD provenance decision.

The negative terminal result is a successful audit outcome. A nonzero exit
means that the evidence could not be loaded or no longer supports the recorded
decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
M27_DIR = ROOT / "research" / "official_topology" / "m27"
REPORT = M27_DIR / "m27_terminal_audit.json"

EXPECTED_DISSERTATION_SHA256 = (
    "c1c86dc1c441fa86dbe6b4b38a521ffb26a5eec3c4eede0f5782508a6ad41160"
)
EXPECTED_DISSERTATION_PAGES = 109
TERMINAL_STATUS = "TERMINAL_M27_EXACT_0BSD_REPLACEMENT_NOT_ACHIEVED"

M23_REPORT = ROOT / "validation" / "official_oracle_comparison_report.json"
M24_REPORT = ROOT / "validation" / "m24_exact_topology_report.json"
M24_RULES = ROOT / "research" / "official_topology" / "m24" / "topology_rules.json"
M26_INTEGRATION = (
    ROOT
    / "research"
    / "official_topology"
    / "m26"
    / "m26_godot_voxel_integration.json"
)
M26_FULL_BUILD = (
    ROOT
    / "research"
    / "official_topology"
    / "m26"
    / "m26_full_godot_voxel_build.json"
)
M3_CORE = ROOT / "research" / "official_topology" / "m3" / "m3_core.py"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return "<external-source>/" + path.name


def normalize_pdf_text(text: str) -> str:
    return " ".join(
        text.replace("\ufb00", "ff")
        .replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .split()
    ).lower()


def first_existing(paths: Iterable[Path]) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def find_dissertation(explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("TRANSVOXEL_DISSERTATION"):
        candidates.append(Path(os.environ["TRANSVOXEL_DISSERTATION"]))
    candidates.extend(
        [
            Path.home()
            / "AppData"
            / "Local"
            / "Temp"
            / "transvoxel_m27_sources"
            / "Lengyel-VoxelTerrain.pdf",
            Path.home()
            / "Documents"
            / "Playground"
            / "transvoxel_godot"
            / "references"
            / "Lengyel-VoxelTerrain.pdf",
        ]
    )
    return first_existing(candidates)


def find_oracle_repo(explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("TRANSVOXEL_ORACLE_REPO"):
        candidates.append(Path(os.environ["TRANSVOXEL_ORACLE_REPO"]))
    candidates.append(
        Path.home()
        / "Documents"
        / "Playground"
        / "transvoxel_godot"
        / "references"
        / "transvoxel_repo"
    )
    return next(
        (
            path
            for path in candidates
            if (path / "LICENSE").is_file()
            and (path / "Transvoxel.cpp").is_file()
        ),
        None,
    )


def source_checks(reader: PdfReader) -> list[Dict[str, Any]]:
    checks = [
        (
            "minimal_triangulation_freedom",
            24,
            16,
            "any minimal cell triangulation is acceptable",
            "The normative goal permits multiple robust minimal interiors.",
        ),
        (
            "preferred_polarity_boundary_rule",
            25,
            17,
            "always connect vertices on adjacent edges sharing an inside corner",
            "The publication fixes ambiguous boundary connectivity.",
        ),
        (
            "regular_alternatives_legal",
            39,
            31,
            "not the only legal triangulation",
            "Most regular classes admit more than one legal interior.",
        ),
        (
            "regular_alternatives_authored_choice",
            40,
            32,
            "chosen to be as dissimilar as possible",
            "The two illustrated alternatives are an authored curvature choice.",
        ),
        (
            "transition_class_ids_arbitrary",
            46,
            38,
            "assigned somewhat arbitrarily",
            "The 73 numeric class IDs are not a geometric invariant.",
        ),
        (
            "transition_boundary_constraints",
            51,
            43,
            "consistent set of rules",
            "Transition full, half, and lateral boundaries are constrained.",
        ),
        (
            "transition_internal_edges_described",
            52,
            44,
            "internal edges",
            "Exact transition interiors are described and illustrated, not uniquely derived by an algorithm.",
        ),
    ]
    results = []
    for check_id, pdf_page, printed_page, phrase, meaning in checks:
        text = normalize_pdf_text(reader.pages[pdf_page - 1].extract_text() or "")
        results.append(
            {
                "id": check_id,
                "pdf_page": pdf_page,
                "printed_page": printed_page,
                "short_phrase_checked": phrase,
                "found": phrase in text,
                "meaning": meaning,
            }
        )
    return results


def count_nonzero_rules(rules: list[Dict[str, Any]]) -> tuple[int, int]:
    nonzero_rules = 0
    nonzero_indexes = 0
    for rule in rules:
        indexes = [int(value) for value in rule.get("option_indexes", [])]
        if any(index != 0 for index in indexes):
            nonzero_rules += 1
        nonzero_indexes += sum(index != 0 for index in indexes)
    return nonzero_rules, nonzero_indexes


def write_failure(errors: list[str]) -> int:
    report = {
        "schema": "boqsc.transvoxel.official_topology.m27.terminal_audit.v1",
        "status": "FAIL_M27_TERMINAL_AUDIT",
        "terminal": False,
        "errors": errors,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    REPORT.write_text(encoded, encoding="utf-8")
    for error in errors:
        print("ERROR", error)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dissertation")
    parser.add_argument("--oracle-repo")
    args = parser.parse_args()

    dissertation = find_dissertation(args.dissertation)
    oracle_repo = find_oracle_repo(args.oracle_repo)
    errors = []
    if dissertation is None:
        errors.append(
            "official dissertation not found; set TRANSVOXEL_DISSERTATION"
        )
    if oracle_repo is None:
        errors.append(
            "official oracle checkout not found; set TRANSVOXEL_ORACLE_REPO"
        )
    for path in (
        M23_REPORT,
        M24_REPORT,
        M24_RULES,
        M26_INTEGRATION,
        M26_FULL_BUILD,
        M3_CORE,
    ):
        if not path.is_file():
            errors.append("missing " + rel(path))
    if errors:
        return write_failure(errors)

    assert dissertation is not None
    assert oracle_repo is not None
    dissertation_sha = sha256_file(dissertation)
    reader = PdfReader(str(dissertation))
    publication_checks = source_checks(reader)
    if dissertation_sha != EXPECTED_DISSERTATION_SHA256:
        errors.append("unexpected dissertation SHA-256: " + dissertation_sha)
    if len(reader.pages) != EXPECTED_DISSERTATION_PAGES:
        errors.append(f"unexpected dissertation page count: {len(reader.pages)}")
    for check in publication_checks:
        if not check["found"]:
            errors.append("publication phrase not found: " + check["id"])

    license_path = oracle_repo / "LICENSE"
    source_path = oracle_repo / "Transvoxel.cpp"
    license_text = license_path.read_text(encoding="utf-8", errors="replace")
    source_header = "\n".join(
        source_path.read_text(encoding="utf-8", errors="replace").splitlines()[:20]
    )
    license_checks = {
        "mit_license_heading": "MIT License" in license_text,
        "copyright_2009_eric_lengyel": (
            "Copyright (c) 2009 Eric Lengyel" in license_text
            and "Copyright 2009 by Eric Lengyel" in source_header
        ),
        "notice_must_be_included": (
            "copyright notice and this permission notice shall be included"
            in license_text.lower()
        ),
    }
    for check_id, passed in license_checks.items():
        if not passed:
            errors.append("official MIT license check failed: " + check_id)

    m23 = read_json(M23_REPORT)
    m24 = read_json(M24_REPORT)
    rules = read_json(M24_RULES)
    integration = read_json(M26_INTEGRATION)
    full_build = read_json(M26_FULL_BUILD)
    regular_rules = rules["regular"]["rules"]
    transition_rules = rules["transition"]["rules"]
    regular_nonzero_rules, regular_nonzero_indexes = count_nonzero_rules(
        regular_rules
    )
    transition_nonzero_rules, transition_nonzero_indexes = count_nonzero_rules(
        transition_rules
    )
    annulus_rules = sum(
        rule.get("kind") == "planar_annulus_zipper"
        for rule in transition_rules
    )

    independent_regular_matches = m23["regular"]["matches"][
        "oriented_topology"
    ]
    independent_transition_matches = m23["transition"]["matches"][
        "oriented_topology"
    ]
    independent_structural_matches = all(
        m23[section]["matches"][metric] == m23[section]["case_count"]
        for section in ("regular", "transition")
        for metric in ("triangle_count", "vertex_count", "vertex_edge_set")
    )
    exact_regular_matches = m24["regular"]["matches"]["oriented_topology"]
    exact_transition_matches = m24["transition"]["matches"][
        "oriented_topology"
    ]
    integration_comparison = integration.get("comparison", {})
    m3_text = M3_CORE.read_text(encoding="utf-8")
    independent_rule_checks = {
        "shortest_diagonal_dynamic_programming": (
            "def triangulate_loop_dp" in m3_text
            and '"shortest_diagonal_dynamic_programming"' in m3_text
        ),
        "nonintersecting_loop_enumeration": (
            "select_nonintersecting_loop_fills" in m3_text
        ),
        "planar_annulus_zipper": "def annulus_candidate" in m3_text,
    }
    for check_id, passed in independent_rule_checks.items():
        if not passed:
            errors.append("independent rule check failed: " + check_id)

    evidence_ok = (
        m23.get("status")
        == "PASS_M23_OFFICIAL_ORACLE_BASELINE_EXACT_REPLACEMENT_NOT_READY"
        and independent_regular_matches == 86
        and independent_transition_matches == 139
        and independent_structural_matches
        and m24.get("status")
        == "PASS_M24_EXACT_REGULAR_TRANSITION_TOPOLOGY"
        and exact_regular_matches == 256
        and exact_transition_matches == 512
        and regular_nonzero_rules == 170
        and transition_nonzero_rules == 50
        and annulus_rules == 1
        and integration.get("status")
        == "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION"
        and integration_comparison.get("mismatch_count") == 0
        and full_build.get("status")
        == "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
    )
    if not evidence_ok:
        errors.append("M23-M26 evidence no longer matches the terminal baseline")
    if errors:
        return write_failure(errors)

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m27.terminal_audit.v1",
        "status": TERMINAL_STATUS,
        "terminal": True,
        "audit_completed": True,
        "meaning": (
            "The exact semantic candidate is technically proven, but the "
            "published normative rules do not uniquely determine the official "
            "interior triangulations. The independent deterministic 0BSD rule "
            "does not reproduce every official case, while the exact M24 "
            "candidate closes those gaps with MIT-oracle-calibrated choices. "
            "Under this project's clean-room provenance standard, the exact "
            "candidate cannot be released as 0BSD."
        ),
        "decision": {
            "exact_0bsd_goal_achieved": False,
            "exact_candidate_0bsd_provenance_cleared": False,
            "technical_semantic_integration_proven": True,
            "functional_0bsd_replacement_remains_available": True,
            "no_further_automatic_milestones": True,
            "terminal": True,
        },
        "publication": {
            "title": "Voxel-Based Terrain for Real-Time Virtual Simulations",
            "official_url": "https://transvoxel.org/Lengyel-VoxelTerrain.pdf",
            "local_source": rel(dissertation),
            "bytes": dissertation.stat().st_size,
            "page_count": len(reader.pages),
            "sha256": dissertation_sha,
            "checks": publication_checks,
            "conclusion": (
                "The prose fixes robust boundary connectivity and permits "
                "multiple legal interiors; the authored exact interiors are "
                "presented in figures and tables rather than uniquely selected "
                "by a published deterministic rule."
            ),
        },
        "independent_0bsd_rule": {
            "implementation": rel(M3_CORE),
            "sha256": sha256_file(M3_CORE),
            "checks": independent_rule_checks,
            "regular_oriented_topology_matches": independent_regular_matches,
            "regular_case_count": 256,
            "regular_exact_gap": 256 - independent_regular_matches,
            "transition_oriented_topology_matches": (
                independent_transition_matches
            ),
            "transition_case_count": 512,
            "transition_exact_gap": 512 - independent_transition_matches,
            "all_counts_and_crossing_edge_sets_match": (
                independent_structural_matches
            ),
            "exact_official_topology_reproduced": False,
        },
        "oracle_calibrated_exact_candidate": {
            "regular_oriented_topology_matches": exact_regular_matches,
            "transition_oriented_topology_matches": exact_transition_matches,
            "regular_rule_count": len(regular_rules),
            "regular_rules_with_nonzero_oracle_option": regular_nonzero_rules,
            "regular_nonzero_option_indexes": regular_nonzero_indexes,
            "transition_representative_rule_count": len(transition_rules),
            "transition_rules_with_nonzero_oracle_option": (
                transition_nonzero_rules
            ),
            "transition_nonzero_option_indexes": transition_nonzero_indexes,
            "transition_annulus_signature_rules": annulus_rules,
            "godot_voxel_records_matched": (
                integration_comparison.get("candidate_record_count")
            ),
            "godot_voxel_mismatches": integration_comparison.get(
                "mismatch_count"
            ),
            "full_gdextension_build": full_build.get("status"),
            "technical_semantic_replacement_proven": True,
            "0bsd_release_cleared": False,
        },
        "official_implementation_license": {
            "license": "MIT",
            "copyright": "Copyright (c) 2009 Eric Lengyel",
            "license_file": rel(license_path),
            "license_sha256": sha256_file(license_path),
            "source_file": rel(source_path),
            "source_sha256": sha256_file(source_path),
            "checks": license_checks,
            "project_provenance_conclusion": (
                "Oracle-calibrated authored selections remain inside the MIT "
                "provenance boundary unless separate permission is obtained."
            ),
        },
        "terminal_paths": [
            {
                "id": "MIT_EXACT",
                "result": (
                    "Use the official exact implementation/data while retaining "
                    "the MIT copyright and permission notice."
                ),
            },
            {
                "id": "0BSD_FUNCTIONAL_NONEXACT",
                "result": (
                    "Use the existing independently derived functional 0BSD "
                    "replacement, without claiming exact official interiors."
                ),
            },
            {
                "id": "EXPLICIT_PERMISSION",
                "result": (
                    "Obtain explicit permission or relicensing for the exact "
                    "authored choices, then perform a new provenance review."
                ),
            },
        ],
        "legal_note": (
            "This is an engineering provenance decision for this repository, "
            "not legal advice."
        ),
        "evidence": {
            "m23": rel(M23_REPORT),
            "m24": rel(M24_REPORT),
            "m24_rules": rel(M24_RULES),
            "m26_integration": rel(M26_INTEGRATION),
            "m26_full_build": rel(M26_FULL_BUILD),
        },
        "errors": [],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    REPORT.write_text(encoded, encoding="utf-8")
    print("M27 terminal audit:", report["status"])
    print("exact 0BSD goal achieved: False")
    print("no further automatic milestones: True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
