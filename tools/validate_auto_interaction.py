#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the Godot automated interaction proof report."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / "godot" / "validation" / "07_auto_interaction" / "auto_interaction.json"
OUT = ROOT / "validation" / "auto_interaction_report.json"


def read(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    issues: List[str] = []
    data: Dict[str, Any] = {}
    if not AUTO.exists():
        issues.append("missing " + rel(AUTO))
    else:
        try:
            data = read(AUTO)
        except Exception as exc:
            issues.append("cannot read auto interaction report: " + repr(exc))
            data = {}
    if data:
        if data.get("status") != "PASS":
            issues.append("auto_interaction status is not PASS")
        if int(data.get("failed_checks", -1)) != 0:
            issues.append("auto_interaction failed_checks is not 0")
        if int(data.get("field_count", 0)) < 6:
            issues.append("auto_interaction field_count < 6")
        if int(data.get("scenario_count", 0)) < 10:
            issues.append("auto_interaction scenario_count < 10")
        if int(data.get("scripted_edits", 0)) < 100:
            issues.append("auto_interaction scripted_edits < 100")
        if int(data.get("check_count", 0)) < 110:
            issues.append("auto_interaction check_count < 110")
        if int(data.get("checked_shared_faces_total", 0)) < 1000:
            issues.append("auto_interaction checked_shared_faces_total < 1000")
        if int(data.get("seam_open_edges", -1)) != 0:
            issues.append("auto_interaction seam_open_edges is not 0")
        if int(data.get("invalid_triangles", -1)) != 0:
            issues.append("auto_interaction invalid_triangles is not 0")
        if int(data.get("degenerate_triangles", -1)) != 0:
            issues.append("auto_interaction degenerate_triangles is not 0")
    result = {
        "schema": "boqsc.transvoxel.auto_interaction_report.v1",
        "status": "PASS" if not issues else "BLOCKED",
        "issues": issues,
        "expected_file": rel(AUTO),
        "summary": {
            "field_count": data.get("field_count"),
            "scenario_count": data.get("scenario_count"),
            "scripted_edits": data.get("scripted_edits"),
            "check_count": data.get("check_count"),
            "failed_checks": data.get("failed_checks"),
            "checked_shared_faces_total": data.get("checked_shared_faces_total"),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("auto interaction validation:", result["status"])
    if issues:
        for issue in issues:
            print(" -", issue)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
