#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate Godot-generated staged runtime dump files when available."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "godot_runtime_data_report.json"
RUNTIME = ROOT / "godot" / "validation" / "01_runtime" / "runtime_dump.json"
MESH = ROOT / "godot" / "validation" / "02_mesh_api" / "mesh_api_dump.json"
SEAM = ROOT / "godot" / "validation" / "03_seam_metrics" / "seam_metrics.json"
AUTO = ROOT / "godot" / "validation" / "07_auto_interaction" / "auto_interaction.json"


def read(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def main() -> int:
    issues: List[str] = []
    if not RUNTIME.exists():
        issues.append("missing " + rel(RUNTIME))
    else:
        data = read(RUNTIME)
        if data.get("status") != "PASS":
            issues.append("runtime_dump status is not PASS")
        if int(data.get("tables", {}).get("transition_cases", 0)) != 512:
            issues.append("runtime_dump transition case count is not 512")
    if not MESH.exists():
        issues.append("missing " + rel(MESH))
    else:
        data = read(MESH)
        if data.get("status") != "PASS":
            issues.append("mesh_api_dump status is not PASS")
        if int(data.get("mesh", {}).get("surface_count", 0)) < 1:
            issues.append("mesh_api_dump has no surface")
    if not SEAM.exists():
        issues.append("missing " + rel(SEAM))
    else:
        data = read(SEAM)
        if data.get("status") != "PASS":
            issues.append("seam_metrics status is not PASS")
        if int(data.get("seam_open_edges", -1)) != 0:
            issues.append("seam_metrics seam_open_edges is not 0")
        if int(data.get("invalid_triangles", -1)) != 0:
            issues.append("seam_metrics invalid_triangles is not 0")
        if int(data.get("degenerate_triangles", -1)) != 0:
            issues.append("seam_metrics degenerate_triangles is not 0")
        if int(data.get("tested_face_directions", 0)) < 6:
            issues.append("seam_metrics tested_face_directions < 6")
        if int(data.get("tested_fields", 0)) < 5:
            issues.append("seam_metrics tested_fields < 5")
    if not AUTO.exists():
        issues.append("missing " + rel(AUTO))
    else:
        data = read(AUTO)
        if data.get("status") != "PASS":
            issues.append("auto_interaction status is not PASS")
        if int(data.get("failed_checks", -1)) != 0:
            issues.append("auto_interaction failed_checks is not 0")
        if int(data.get("scripted_edits", 0)) < 100:
            issues.append("auto_interaction scripted_edits < 100")
    result = {
        "status": "PASS" if not issues else "BLOCKED",
        "issues": issues,
        "expected_files": [rel(RUNTIME), rel(MESH), rel(SEAM), rel(AUTO)],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("godot runtime data:", result["status"])
    return 0 if not issues else 2

if __name__ == "__main__":
    raise SystemExit(main())
