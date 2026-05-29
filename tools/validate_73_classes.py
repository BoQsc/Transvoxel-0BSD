#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Audit whether this project has proven the official 73 transition equivalence classes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "equivalence_class_report.json"
MD = ROOT / "validation" / "equivalence_class_report.md"


def main() -> int:
    tv = json.loads((ROOT / "generated" / "transvoxel_tables.json").read_text(encoding="utf-8"))
    transition = tv.get("transition", {})
    case_count = int(transition.get("case_count", 0))
    class_count = int(transition.get("class_count", 0))
    compression = str(tv.get("compression", ""))
    official_expected = 73
    status = "PASS_INTERNAL_DIRECT_MAPPING_NOT_OFFICIAL_73"
    official_equivalence = "NOT_PROVEN"
    reasons = []
    if case_count != 512:
        status = "FAIL"
        reasons.append(f"transition case count is {case_count}, expected 512")
    if class_count != official_expected:
        reasons.append(f"current class_count is {class_count}; official Transvoxel uses 73 transition equivalence classes")
    if "one-class-per-case" in compression or class_count == case_count:
        reasons.append("current export intentionally uses direct one-class-per-case mapping for readability/provenance")
    report = {
        "schema": "boqsc.transvoxel.equivalence_class_audit.v1",
        "status": status,
        "official_equivalence_proof": official_equivalence,
        "case_count": case_count,
        "current_class_count": class_count,
        "official_transition_equivalence_class_count": official_expected,
        "compression": compression,
        "reasons": reasons,
        "meaning": "This audit keeps the claim honest: the project covers all 512 transition cases, but it does not yet prove the official 73-class mapping.",
        "pass_condition_for_future_official_equivalence": [
            "derive 73 canonical classes without copying MIT table values",
            "prove every one of the 512 cases maps to one of those classes by documented symmetry/inversion transforms",
            "prove transformed triangle winding and vertex references round-trip to the direct 512-case canonical table",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    MD.write_text("\n".join([
        "# 73-Class Equivalence Audit",
        "",
        f"Status: **{status}**",
        "",
        f"Current transition cases: `{case_count}`",
        f"Current transition classes: `{class_count}`",
        f"Official transition equivalence classes: `{official_expected}`",
        "",
        "Official equivalence proof: **NOT_PROVEN**",
        "",
        "Reasons:",
        *[f"- {r}" for r in reasons],
        "",
        "This is not a runtime failure. It means the project currently proves a direct 512-case generated table, not the official 73-class compressed mapping.",
        "",
    ]), encoding="utf-8")
    print("73-class audit:", status)
    return 0 if case_count == 512 else 1


if __name__ == "__main__":
    raise SystemExit(main())
