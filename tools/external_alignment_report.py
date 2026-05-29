#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "validation" / "external_alignment_report.json"


def read_json(rel: str) -> dict:
    path = ROOT / rel
    if not path.exists():
        return {"missing": True, "path": rel}
    return json.loads(path.read_text(encoding="utf-8"))


def status_from_bool(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> int:
    tables = read_json("generated/transvoxel_tables.json")
    boundary = read_json("validation/boundary_report.json")
    neighbor = read_json("validation/neighbor_report.json")
    chunk = read_json("validation/chunk_report.json")
    proof = read_json("validation/proof_report.json")
    auto = read_json("validation/auto_interaction_report.json")
    auto_raw = read_json("godot/validation/07_auto_interaction/auto_interaction.json")
    prod = read_json("proof/production_gate.json")

    checks = []

    regular_cases = tables.get("regular", {}).get("case_count")
    transition_cases = tables.get("transition", {}).get("case_count")
    checks.append({
        "requirement": "regular cell case count is 256",
        "source_basis": "marching-cubes / Transvoxel regular-cell practice",
        "value": regular_cases,
        "status": status_from_bool(regular_cases == 256),
    })
    checks.append({
        "requirement": "transition cell case count is 512",
        "source_basis": "Transvoxel uses 9 transition face signs, giving 512 cases",
        "value": transition_cases,
        "status": status_from_bool(transition_cases == 512),
    })
    checks.append({
        "requirement": "all transition boundaries match expected fingerprints",
        "source_basis": "transition cells must seal high/low LOD boundaries",
        "value": boundary.get("failure_count"),
        "status": status_from_bool(boundary.get("status") == "PASS" and boundary.get("failure_count") == 0),
    })
    checks.append({
        "requirement": "neighboring transition cells have matching side contours",
        "source_basis": "transition strips must not crack between adjacent transition cells",
        "value": {
            "determinism_failures": neighbor.get("determinism_failures"),
            "opposite_face_failures": neighbor.get("opposite_face_failures"),
        },
        "status": status_from_bool(neighbor.get("status") == "PASS"),
    })
    checks.append({
        "requirement": "chunk-strip scalar-field proof passes",
        "source_basis": "real terrain fields should not create strip side cracks",
        "value": {
            "shared_faces_checked": chunk.get("shared_faces_checked"),
            "fields": chunk.get("fields"),
            "failures": chunk.get("failure_count"),
        },
        "status": status_from_bool(chunk.get("status") == "PASS" and chunk.get("failure_count") == 0),
    })
    auto_summary = auto.get("summary", {}) if isinstance(auto.get("summary", {}), dict) else {}
    auto_failed = auto.get("failed_checks", auto_summary.get("failed_checks", auto_raw.get("failed_checks")))
    auto_edits = auto.get("scripted_edits", auto_summary.get("scripted_edits", auto_raw.get("scripted_edits")))
    auto_checks = auto.get("check_count", auto_summary.get("check_count", auto_raw.get("check_count")))
    auto_status = str(auto.get("status", auto_raw.get("status", ""))).upper()

    checks.append({
        "requirement": "automated dig/add interaction proof passes when present",
        "source_basis": "dynamic terrain should support local retriangulation without seam failures",
        "value": {
            "status": auto_status,
            "failed_checks": auto_failed,
            "scripted_edits": auto_edits,
            "check_count": auto_checks,
        },
        "status": "SKIPPED" if auto.get("missing") and auto_raw.get("missing") else status_from_bool(auto_status == "PASS" and auto_failed == 0 and (auto_edits or 0) >= 100),
    })
    prod_status = str(prod.get("status", "")).upper()
    checks.append({
        "requirement": "full production gate passes when full data exists",
        "source_basis": "release gate for this repository",
        "value": prod.get("status"),
        "status": "SKIPPED" if prod.get("missing") or prod_status in ("", "NOT_RUN") else status_from_bool(prod_status == "PASS"),
    })

    pass_fail = [c for c in checks if c["status"] in ("PASS", "FAIL")]
    failed = [c for c in pass_fail if c["status"] != "PASS"]

    report = {
        "schema": "boqsc.transvoxel.external_alignment_report.v1",
        "status": "PASS" if not failed else "FAIL",
        "summary": "Checks this clean-room 0BSD core against externally derived Transvoxel-style outcome requirements.",
        "important_limitations": [
            "This report does not prove byte/table identity with Eric Lengyel's MIT Transvoxel.cpp.",
            "This report does not prove official 73-class compression.",
            "This report does not prove final game art quality or large-world streaming performance.",
        ],
        "checks": checks,
        "proof_report_ok": proof.get("ok"),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("external alignment:", report["status"])
    print(REPORT)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
