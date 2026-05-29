#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""No-copy research scaffold for reference sign/orientation convention.

This records which convention questions remain open. It does not inspect or
copy external table values.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "official_reference_convention_research.json"

def main() -> int:
    report = {
        "schema": "boqsc.transvoxel.official_reference_convention_research.v1",
        "status": "REFERENCE_EQUIVALENCE_NOT_PROVEN",
        "internal_convention_status": "PASS_IN_CURRENT_CORE",
        "official_convention_status": "NOT_PROVEN",
        "questions": [
            "Which side is considered high-resolution versus low-resolution in the official table orientation?",
            "Which sign means inside/solid in official table case bits?",
            "Which winding convention is assumed for front-facing triangles?",
            "How are inverted cases represented and wound?",
            "How are lateral transition faces oriented between neighboring transition cells?",
        ],
        "no_copy_rule": "Research must use public structural descriptions, independent generated probes, and diagrams; not official MIT table values.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("official reference convention:", report["status"])
    print(OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
