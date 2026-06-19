#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M22: exact-compatibility claim-boundary lock."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M22_DIR = ROOT / "research" / "official_topology" / "m22"
REPORT = M22_DIR / "m22_report.json"
RESULTS = M22_DIR / "results.md"
PASS_STATUS = "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"

READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
CLAIM_BOUNDARY = ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
CONSUMER = ROOT / "validation" / "consumer_compatibility_report.json"
TRANSVOXEL = ROOT / "validation" / "transvoxel_report.json"
GODOT_RUNTIME = ROOT / "validation" / "godot_runtime_data_report.json"
PROJECT_TRACKS = ROOT / "validation" / "project_tracks_report.json"


def sanitize(output: str) -> str:
    return (
        output.replace(str(ROOT), "<repo>")
        .replace(str(ROOT).replace("\\", "/"), "<repo>")
        .replace(str(Path(sys.executable)), "python")
    )


def stable_command(command: List[str]) -> List[str]:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    out: List[str] = []
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            out.append("python")
        else:
            out.append(item.replace(root_native, "<repo>").replace(root_forward, "<repo>"))
    return out


def run_step(command: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    return {
        "command": stable_command(command),
        "returncode": proc.returncode,
        "output": sanitize(proc.stdout),
    }


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_results(report: Dict[str, Any]) -> None:
    readiness = report.get("readiness_report", {})
    boundary = report.get("claim_boundary_report", {})
    lines = [
        "# M22 Exact Compatibility Claim Boundary",
        "",
        "M22 keeps the M21 functional replacement evidence green and locks the stronger exact official-compatibility claims behind explicit blockers.",
        "",
        f"- Status: `{report['status']}`",
        f"- Transvoxel export validation: `{report.get('transvoxel_status')}`",
        f"- Consumer compatibility: `{report.get('consumer_status')}`",
        f"- Claim-boundary validation: `{boundary.get('status')}`",
        f"- Readiness: `{readiness.get('status')}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "## Allowed now",
        "",
        boundary.get("claim_contract", {}).get("allowed_now", ""),
        "",
        "## Still not allowed",
        "",
    ]
    for item in boundary.get("claim_contract", {}).get("not_allowed_now", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "No zip/package artifact is built by this milestone runner.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    M22_DIR.mkdir(parents=True, exist_ok=True)
    steps = [
        run_step([sys.executable, "tools/export_transvoxel.py"]),
        run_step([sys.executable, "tools/sync_godot_tables.py"]),
        run_step([sys.executable, "tools/validate_transvoxel.py"]),
        run_step([sys.executable, "tools/test_core_c.py"]),
        run_step([sys.executable, "tools/test_m4_backend_c.py"]),
        run_step([sys.executable, "tools/test_m4_terrain_c.py"]),
        run_step([sys.executable, "tools/test_consumer_compatibility.py"]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
        run_step([sys.executable, "tools/validate_exact_compatibility_claim_boundary.py"]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_godot_dump.py"]),
        run_step([sys.executable, "tools/project_tracks_report.py"]),
    ]

    readiness = read_json(READINESS)
    boundary = read_json(CLAIM_BOUNDARY)
    consumer = read_json(CONSUMER)
    transvoxel = read_json(TRANSVOXEL)
    godot_runtime = read_json(GODOT_RUNTIME)
    project_tracks = read_json(PROJECT_TRACKS)

    final_ok = (
        all(step["returncode"] == 0 for step in steps)
        and transvoxel.get("ok") is True
        and consumer.get("status") == "PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY"
        and boundary.get("status") == PASS_STATUS
        and readiness.get("status")
        == "READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_EXACT_COMPATIBILITY_BLOCKED"
        and readiness.get("decisions", {}).get("functional_full_replacement_ready") is True
        and readiness.get("decisions", {}).get("exact_table_compatible_replacement_ready") is False
        and readiness.get("decisions", {}).get("exact_compatibility_claim_boundary_documented") is True
        and readiness.get("next_milestone", {}).get("id")
        in {
            "M23_OFFICIAL_ORACLE_BASELINE",
            "M24_EXACT_TOPOLOGY_CONVERGENCE",
        }
        and set(readiness.get("blocking_gate_ids", []))
        == {
            "official_class_id_mapping",
            "official_vertex_encoding_equivalence",
            "official_triangle_triangulation_identity",
            "official_regular_table_identity",
            "official_transvoxel_cpp_byte_identity",
        }
        and godot_runtime.get("status") == "PASS"
        and project_tracks.get("status") == "PASS"
    )

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m22.report.v1",
        "status": PASS_STATUS if final_ok else "FAIL_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY",
        "meaning": (
            "M22 documents and machine-checks the exact-compatibility claim "
            "boundary: functional replacement is ready through the public "
            "C/C++ API, while exact official Transvoxel.cpp class/table/"
            "encoding/byte identity remains unclaimed."
        ),
        "functional_replacement_claim": "ALLOWED",
        "exact_table_compatible_replacement_claim": "NOT_ALLOWED",
        "transvoxel_status": transvoxel.get("status"),
        "consumer_status": consumer.get("status"),
        "claim_boundary_report": boundary,
        "readiness_report": readiness,
        "godot_runtime_report": godot_runtime,
        "project_tracks_report": project_tracks,
        "steps": steps,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report)
    print()
    print("M22:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
