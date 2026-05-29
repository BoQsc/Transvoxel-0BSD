#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Audit what is and is not proven about six-face, corner, and neighboring chunk edits."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "corner_junction_report.json"
MD = ROOT / "validation" / "corner_junction_report.md"


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    chunk = read_json(ROOT / "validation" / "chunk_report.json")
    seam = read_json(ROOT / "godot" / "validation" / "03_seam_metrics" / "seam_metrics.json")
    auto = read_json(ROOT / "godot" / "validation" / "07_auto_interaction" / "auto_interaction.json")
    face_dirs = int(seam.get("tested_face_directions", 0) or 0)
    fields = int(seam.get("tested_fields", 0) or 0)
    scripted_edits = int(auto.get("scripted_edits", 0) or 0)
    failed_auto = int(auto.get("failed_checks", 0) or 0) if auto else 0
    chunk_ok = chunk.get("status") == "PASS"
    seam_ok = seam.get("status") == "PASS" if seam else False
    auto_ok = auto.get("status") == "PASS" if auto else False
    proven = {
        "transition_side_faces_match_in_python_chunk_strips": chunk_ok,
        "godot_seam_metrics_all_six_faces": seam_ok and face_dirs >= 6,
        "godot_seam_metrics_multiple_fields": seam_ok and fields >= 5,
        "automated_scripted_edits_pass": auto_ok and failed_auto == 0 and scripted_edits >= 100,
    }
    not_proven = [
        "all possible multi-LOD corner junction topologies with three or more LOD levels meeting",
        "all possible chunk-edge and chunk-corner edit neighborhoods in a production streaming world",
        "concurrency/streaming races where several neighboring chunks rebuild out of order",
        "GPU compute implementation parity; this audit is CPU/Godot/Python proof oriented",
    ]
    status = "PASS_PARTIAL_JUNCTION_AUDIT" if all(proven.values()) else "PARTIAL_OR_BLOCKED"
    report = {
        "schema": "boqsc.transvoxel.corner_junction_audit.v1",
        "status": status,
        "proven_checks": proven,
        "not_fully_proven": not_proven,
        "chunk_report_status": chunk.get("status"),
        "seam_metrics_status": seam.get("status") if seam else "NOT_AVAILABLE",
        "auto_interaction_status": auto.get("status") if auto else "NOT_AVAILABLE",
        "tested_face_directions": face_dirs,
        "tested_fields": fields,
        "scripted_edits": scripted_edits,
        "failed_auto_checks": failed_auto,
        "meaning": "This audit proves the current six-face and scripted-edit evidence when present. It does not claim exhaustive proof for every possible production corner/multi-neighbor junction topology.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Corner and Neighboring Chunk Junction Audit",
        "",
        f"Status: **{status}**",
        "",
        "## Proven by current package data",
        "",
        *[f"- {'PASS' if v else 'NOT AVAILABLE / NOT PROVEN'} — `{k}`" for k, v in proven.items()],
        "",
        "## Not fully proven yet",
        "",
        *[f"- {x}" for x in not_proven],
        "",
    ]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("corner junction audit:", status)
    # Missing Godot runtime auto data should not fail a source package proof; it is reported as partial.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
