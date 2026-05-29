#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Audit whether reference sign/orientation convention equivalence has been proven."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "reference_convention_report.json"
MD = ROOT / "validation" / "reference_convention_report.md"


def main() -> int:
    transition = json.loads((ROOT / "generated" / "transition_tables.json").read_text(encoding="utf-8"))
    high_samples = [s for s in transition.get("sample_positions", []) if s.get("kind") == "full_resolution_face"]
    sample_count = len(transition.get("sample_positions", []))
    case_count = len(transition.get("cases", []))
    checks = {
        "transition_case_count_is_512": case_count == 512,
        "full_resolution_transition_samples_are_9": len(high_samples) == 9,
        "total_transition_samples_are_14": sample_count == 14,
        "half_resolution_corner_sources_exist": bool(transition.get("half_resolution_corner_sign_sources")),
        "synthetic_center_source_exists": bool(transition.get("synthetic_center_sign_source")),
    }
    internal_ok = all(checks.values())
    report = {
        "schema": "boqsc.transvoxel.reference_convention_audit.v1",
        "status": "PASS_INTERNAL_CONVENTION" if internal_ok else "FAIL_INTERNAL_CONVENTION",
        "reference_equivalence_status": "NOT_PROVEN",
        "checks": checks,
        "reason": "The project intentionally does not load or compare against Eric Lengyel's MIT Transvoxel.cpp tables. Therefore exact reference sign/orientation convention equivalence is not proven.",
        "future_pass_condition": [
            "write an independent convention document for sample order, face orientation, case-bit meaning, and inside/outside sign",
            "derive transforms from that document to the published dissertation diagrams without copying table values",
            "validate a public-domain reference-case corpus if one becomes available or is generated independently",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Reference Convention Audit",
        "",
        f"Status: **{report['status']}**",
        "",
        "Reference equivalence status: **NOT_PROVEN**",
        "",
        "## Internal convention checks",
        "",
        *[f"- {'PASS' if v else 'FAIL'} — `{k}`" for k, v in checks.items()],
        "",
        "This project proves its own sign/orientation convention is internally consistent. It does not yet prove exact convention identity with the MIT table file.",
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("reference convention audit:", report["status"], "reference_equivalence=NOT_PROVEN")
    return 0 if internal_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
