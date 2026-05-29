#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Audit triangle degenerates, duplicates, and complement winding consistency."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from _audit_geom import case_triangles, dot, length2, load_table, triangle_normal, tri_unordered_key

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "winding_normals_report.json"
MD = ROOT / "validation" / "winding_normals_report.md"
EPS = 1.0e-12


def audit_table(name: str, filename: str, complement_mask: int) -> Dict[str, object]:
    table = load_table(ROOT, filename)
    cases = table["cases"]  # type: ignore[index]
    duplicate_examples: List[object] = []
    degenerate_examples: List[object] = []
    complement_mismatch_examples: List[object] = []
    triangle_count = 0
    for idx, case in enumerate(cases):  # type: ignore[union-attr]
        tris = case_triangles(table, case)
        triangle_count += len(tris)
        seen = set()
        for ti, tri in enumerate(tris):
            n = triangle_normal(tri)
            if length2(n) <= EPS and len(degenerate_examples) < 20:
                degenerate_examples.append({"case": idx, "triangle": ti})
            key = tri_unordered_key(tri)
            if key in seen and len(duplicate_examples) < 20:
                duplicate_examples.append({"case": idx, "triangle": ti, "key": key})
            seen.add(key)
    # Complement cases should expose the same geometric triangles with opposite normals.
    for idx, case in enumerate(cases):  # type: ignore[union-attr]
        other = cases[complement_mask ^ idx]
        a_tris = {tri_unordered_key(t): t for t in case_triangles(table, case)}
        b_tris = {tri_unordered_key(t): t for t in case_triangles(table, other)}
        if set(a_tris) != set(b_tris):
            if len(complement_mismatch_examples) < 20:
                complement_mismatch_examples.append({"case": idx, "reason": "geometry differs from complement"})
            continue
        for key, tri in a_tris.items():
            n1 = triangle_normal(tri)
            n2 = triangle_normal(b_tris[key])
            if length2(n1) > EPS and length2(n2) > EPS and dot(n1, n2) >= -EPS:
                if len(complement_mismatch_examples) < 20:
                    complement_mismatch_examples.append({"case": idx, "reason": "complement normal is not opposite", "triangle_key": key})
                break
    ok = not duplicate_examples and not degenerate_examples and not complement_mismatch_examples
    return {
        "name": name,
        "ok": ok,
        "case_count": len(cases),  # type: ignore[arg-type]
        "triangle_count": triangle_count,
        "duplicate_triangle_examples": duplicate_examples,
        "degenerate_triangle_examples": degenerate_examples,
        "complement_winding_mismatch_examples": complement_mismatch_examples,
        "meaning": "Checks generated table geometry for duplicate/degenerate triangles and verifies complement cases expose opposite normals. This proves internal winding consistency, not identity with an external reference table.",
    }


def main() -> int:
    reports = [
        audit_table("regular", "regular_tables.json", 255),
        audit_table("transition", "transition_tables.json", 511),
    ]
    ok = all(bool(r["ok"]) for r in reports)
    report = {
        "schema": "boqsc.transvoxel.winding_normals_audit.v1",
        "status": "PASS" if ok else "FAIL",
        "tables": reports,
        "reference_orientation_equivalence": "NOT_PROVEN",
        "meaning": "Internal generated-table winding/normal audit. It does not prove the same sign convention as Eric Lengyel's MIT tables.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# Winding and Normals Audit", "", f"Status: **{report['status']}**", ""]
    for r in reports:
        lines += [
            f"## {r['name']}",
            "",
            f"Cases: `{r['case_count']}`",
            f"Triangles: `{r['triangle_count']}`",
            f"Degenerate examples: `{len(r['degenerate_triangle_examples'])}`",
            f"Duplicate examples: `{len(r['duplicate_triangle_examples'])}`",
            f"Complement winding mismatch examples: `{len(r['complement_winding_mismatch_examples'])}`",
            "",
        ]
    lines += ["Reference orientation equivalence: **NOT_PROVEN**", ""]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("winding/normals audit:", report["status"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
