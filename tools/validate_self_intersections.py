#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Conservative non-adjacent triangle self-intersection audit for generated cases."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from _audit_geom import case_triangles, load_table, triangles_intersect_nonadjacent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "self_intersection_report.json"
MD = ROOT / "validation" / "self_intersection_report.md"


def audit_table(name: str, filename: str) -> Dict[str, object]:
    table = load_table(ROOT, filename)
    failures: List[object] = []
    pair_count = 0
    case_count = 0
    for ci, case in enumerate(table["cases"]):  # type: ignore[index]
        case_count += 1
        tris = case_triangles(table, case)
        for i in range(len(tris)):
            for j in range(i + 1, len(tris)):
                pair_count += 1
                if triangles_intersect_nonadjacent(tris[i], tris[j]):
                    if len(failures) < 30:
                        failures.append({"case": ci, "triangle_a": i, "triangle_b": j})
    return {
        "name": name,
        "ok": not failures,
        "case_count": case_count,
        "triangle_pairs_checked": pair_count,
        "failure_count": len(failures),
        "failure_examples": failures,
        "meaning": "Checks non-adjacent triangle pairs inside each generated case for obvious intersections. Adjacent triangles sharing vertices are ignored.",
    }


def main() -> int:
    reports = [audit_table("regular", "regular_tables.json"), audit_table("transition", "transition_tables.json")]
    ok = all(bool(r["ok"]) for r in reports)
    report = {
        "schema": "boqsc.transvoxel.self_intersection_audit.v1",
        "status": "PASS" if ok else "FAIL",
        "tables": reports,
        "limitations": [
            "This is a conservative generated-case geometry audit, not a formal computational geometry proof for all floating point interpolation values.",
            "It uses midpoint edge vertices because the current generated tables store sample-edge references, not arbitrary density interpolation positions.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# Self-Intersection Audit", "", f"Status: **{report['status']}**", ""]
    for r in reports:
        lines += [
            f"## {r['name']}",
            "",
            f"Cases: `{r['case_count']}`",
            f"Triangle pairs checked: `{r['triangle_pairs_checked']}`",
            f"Failures: `{r['failure_count']}`",
            "",
        ]
    lines += ["## Limitations", "", *[f"- {x}" for x in report["limitations"]], ""]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("self-intersection audit:", report["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
