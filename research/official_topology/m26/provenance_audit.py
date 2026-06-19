#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Record the M26 exact-candidate provenance decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
M24_RULES = (
    ROOT / "research" / "official_topology" / "m24" / "topology_rules.json"
)
M25_LAYOUT = (
    ROOT
    / "research"
    / "official_topology"
    / "m25"
    / "generated"
    / "m25_compatible_layout.json"
)
REPORT = (
    ROOT
    / "research"
    / "official_topology"
    / "m26"
    / "m26_provenance_audit.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rules = json.loads(M24_RULES.read_text(encoding="utf-8"))
    layout = json.loads(M25_LAYOUT.read_text(encoding="utf-8"))
    oracle_calibrated = (
        "oracle" in rules
        and "calibrate" in str(rules.get("meaning", "")).lower()
    )
    cleared = not oracle_calibrated
    report = {
        "schema": "boqsc.transvoxel.m26.provenance_audit.v1",
        "status": "PASS_M26_PROVENANCE_AUDIT_BLOCKED",
        "decision": {
            "exact_candidate_0bsd_provenance_cleared": cleared,
            "release_exact_candidate_as_0bsd": cleared,
            "generator_code_is_0bsd": True,
            "generated_exact_data_is_research_only": not cleared,
        },
        "blocking_reason": (
            "M24 stores oracle-calibrated triangulation option indexes. "
            "Although boundary loops and candidate enumeration are "
            "independent, the exact choice among valid fillings is not yet "
            "derived from an independent published rule."
            if oracle_calibrated
            else None
        ),
        "required_resolution": (
            "Replace every oracle-calibrated option index with a deterministic "
            "independent selection rule and revalidate all 768 cases, or "
            "obtain explicit legal/provenance clearance."
            if oracle_calibrated
            else None
        ),
        "inputs": {
            "m24_rules_sha256": sha256(M24_RULES),
            "m25_layout_sha256": sha256(M25_LAYOUT),
            "m24_generated_rule_license_status": rules.get(
                "generated_rule_license_status"
            ),
            "m25_generated_data_license_status": layout.get(
                "generated_data_license_status"
            ),
        },
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("M26 provenance audit:", report["status"])
    print(
        "exact candidate 0BSD cleared:",
        report["decision"]["exact_candidate_0bsd_provenance_cleared"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
