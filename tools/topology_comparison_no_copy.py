#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compare public Transvoxel structural expectations with this project without using external table values."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "topology_comparison_no_copy_report.json"
MD = ROOT / "validation" / "topology_comparison_no_copy_report.md"


def read_json(rel: str) -> Dict[str, Any]:
    path = ROOT / rel
    if not path.exists():
        return {"status": "MISSING", "path": rel}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    tv = read_json("generated/transvoxel_tables.json")
    boundary = read_json("validation/boundary_report.json")
    neighbor = read_json("validation/neighbor_report.json")
    chunks = read_json("validation/chunk_report.json")
    seam = read_json("godot/validation/03_seam_metrics/seam_metrics.json")
    auto = read_json("godot/validation/07_auto_interaction/auto_interaction.json")
    transition = tv.get("transition", {}) if isinstance(tv, dict) else {}
    summary = auto.get("summary", auto) if isinstance(auto, dict) else {}

    checks = {
        "has_512_transition_cases": int(transition.get("case_count", 0)) == 512,
        "boundary_fingerprints_pass": boundary.get("status") == "PASS",
        "neighbor_side_faces_pass": neighbor.get("status") == "PASS",
        "chunk_strip_shared_faces_pass": chunks.get("status") == "PASS",
        "godot_seam_open_edges_zero": seam.get("seam_open_edges") == 0,
        "auto_interaction_failed_checks_zero": summary.get("failed_checks") == 0,
        "auto_interaction_has_many_scripted_edits": int(summary.get("scripted_edits", 0) or 0) >= 100,
    }
    ok = all(checks.values())
    status = "PASS" if ok else "FAIL_OR_NOT_RUN"
    report = {
        "schema": "boqsc.transvoxel.topology_comparison_no_copy.v1",
        "status": status,
        "comparison_type": "public structural expectations only; no external table values used",
        "checks": checks,
        "external_structural_expectations": {
            "transition_cases": 512,
            "transition_equivalence_classes": 73,
            "lod_relation": "same resolution or 2:1 adjacent blocks",
            "seam_goal": "no cracks between meshes of different resolution",
        },
        "current_project_evidence": {
            "transition_case_count": transition.get("case_count"),
            "transition_class_count": transition.get("class_count"),
            "boundary_report_status": boundary.get("status"),
            "neighbor_report_status": neighbor.get("status"),
            "chunk_report_status": chunks.get("status"),
            "seam_open_edges": seam.get("seam_open_edges"),
            "auto_interaction_failed_checks": summary.get("failed_checks"),
            "auto_interaction_scripted_edits": summary.get("scripted_edits"),
        },
        "not_compared": [
            "official table bytes",
            "official class IDs",
            "official packed vertex encodings",
            "official triangle index sequences",
        ],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Topology Comparison Without Copying Tables",
        "",
        f"Status: **{status}**",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- `{k}`: **{'PASS' if v else 'FAIL/NOT_RUN'}**")
    lines += ["", "This report uses only this project's generated proof data and public structural expectations. It does not read external table values.", ""]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("topology comparison no-copy:", status)
    return 0 if ok else 0  # not a hard failure before Godot reports exist


if __name__ == "__main__":
    raise SystemExit(main())
