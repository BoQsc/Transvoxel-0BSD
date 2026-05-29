#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Check whether enough non-visual data exists to claim production proof.

This intentionally fails/blocks until Godot runtime and real seam data are
provided. A screenshot is not enough. The gate wants machine-readable numbers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def status_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = read_json(path)
    except Exception:
        return False
    status = str(data.get("status", "")).upper()
    if status == "PASS":
        return True
    if data.get("ok") is True:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="proof/production_gate.json")
    args = parser.parse_args()

    required_pass_reports = [
        ROOT / "validation" / "validation_report.json",
        ROOT / "validation" / "all_tables_report.json",
        ROOT / "validation" / "transvoxel_report.json",
        ROOT / "validation" / "boundary_report.json",
        ROOT / "validation" / "neighbor_report.json",
        ROOT / "validation" / "chunk_report.json",
        ROOT / "validation" / "godot_project_report.json",
        ROOT / "validation" / "proof_report.json",
        ROOT / "validation" / "auto_interaction_report.json",
    ]

    missing_or_failed: List[str] = []
    for path in required_pass_reports:
        if not status_ok(path):
            missing_or_failed.append(str(path.relative_to(ROOT)))

    expected_data_files = [
        ROOT / "proof" / "proof_dump.json",
        ROOT / "godot" / "validation" / "01_runtime" / "runtime_dump.json",
        ROOT / "godot" / "validation" / "02_mesh_api" / "mesh_api_dump.json",
        ROOT / "godot" / "validation" / "03_seam_metrics" / "seam_metrics.json",
        ROOT / "godot" / "validation" / "07_auto_interaction" / "auto_interaction.json",
    ]
    missing_data = [str(p.relative_to(ROOT)) for p in expected_data_files if not p.exists()]

    seam_reasons: List[str] = []
    seam_path = ROOT / "godot" / "validation" / "03_seam_metrics" / "seam_metrics.json"
    if seam_path.exists():
        try:
            seam = read_json(seam_path)
            if int(seam.get("seam_open_edges", -1)) != 0:
                seam_reasons.append("seam_open_edges is not 0")
            if int(seam.get("invalid_triangles", -1)) != 0:
                seam_reasons.append("invalid_triangles is not 0")
            if int(seam.get("degenerate_triangles", -1)) != 0:
                seam_reasons.append("degenerate_triangles is not 0")
            if int(seam.get("tested_face_directions", 0)) < 6:
                seam_reasons.append("tested_face_directions < 6")
            if int(seam.get("tested_fields", 0)) < 5:
                seam_reasons.append("tested_fields < 5")
        except Exception as exc:
            seam_reasons.append("seam_metrics read error: " + repr(exc))


    auto_path = ROOT / "godot" / "validation" / "07_auto_interaction" / "auto_interaction.json"
    if auto_path.exists():
        try:
            auto = read_json(auto_path)
            if str(auto.get("status", "")).upper() != "PASS":
                seam_reasons.append("auto_interaction status is not PASS")
            if int(auto.get("failed_checks", -1)) != 0:
                seam_reasons.append("auto_interaction failed_checks is not 0")
            if int(auto.get("scripted_edits", 0)) < 100:
                seam_reasons.append("auto_interaction scripted_edits < 100")
            if int(auto.get("check_count", 0)) < 110:
                seam_reasons.append("auto_interaction check_count < 110")
        except Exception as exc:
            seam_reasons.append("auto_interaction read error: " + repr(exc))

    blocked = bool(missing_or_failed or missing_data or seam_reasons)
    result: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.production_gate.v1",
        "status": "BLOCKED" if blocked else "PASS",
        "meaning": "PASS here means enough non-visual data exists to start trusting visual validation. It is not a gameplay performance certification.",
        "missing_or_failed_reports": missing_or_failed,
        "missing_data_files": missing_data,
        "seam_reasons": seam_reasons,
        "hard_requirements": {
            "seam_open_edges": 0,
            "invalid_triangles": 0,
            "degenerate_triangles": 0,
            "tested_face_directions_minimum": 6,
            "tested_fields_minimum": 5,
            "requires_godot_runtime_dump": True,
            "requires_godot_mesh_api_dump": True,
            "requires_godot_auto_interaction": True,
            "auto_interaction_scripted_edits_minimum": 100,
            "auto_interaction_failed_checks": 0,
        },
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("production gate:", result["status"])
    if blocked:
        print("blocked reasons written to", out)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
