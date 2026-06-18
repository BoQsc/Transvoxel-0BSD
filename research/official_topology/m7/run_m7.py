#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M7: selectable M4 backend through the normal C API."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
M7_DIR = ROOT / "research" / "official_topology" / "m7"
M6_REPORT = ROOT / "research" / "official_topology" / "m6" / "m6_report.json"
C_REPORT = M7_DIR / "m7_c_validation.json"
M7_REPORT = M7_DIR / "m7_report.json"
RESULTS = M7_DIR / "results.md"


def run_step(command: List[str]) -> Dict[str, object]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    return {
        "command": command,
        "returncode": proc.returncode,
        "output": proc.stdout,
    }


def read_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_results(report: Dict[str, object], c_report: Dict[str, object]) -> None:
    switch = c_report.get("switch", {})
    seam = c_report.get("seam", {})
    lines = [
        "# M7 Normal API Backend Switch",
        "",
        "M7 makes the M4 candidate backend selectable through the normal `tv_build_transition_cell()` C API.",
        "",
        f"- Status: `{report['status']}`",
        f"- C validation: `{c_report['status']}`",
        f"- Compiler: `{c_report.get('compiler', 'NOT_AVAILABLE')}`",
        "",
        "## Backend switch",
        "",
        f"- Cases checked: `{switch.get('cases')}`",
        f"- Default vertices: `{switch.get('default_vertices')}`",
        f"- Default triangles: `{switch.get('default_triangles')}`",
        f"- M4 vertices through normal API: `{switch.get('m4_vertices')}`",
        f"- M4 triangles through normal API: `{switch.get('m4_triangles')}`",
        f"- Count differences: `{switch.get('count_differences')}`",
        f"- Default restored after uninstall: `{switch.get('restored_default')}`",
        "",
        "## Normal API M4 seam validation",
        "",
        f"- Strip builds: `{seam.get('builds')}`",
        f"- Shared faces checked: `{seam.get('shared_faces')}`",
        f"- Seam failures: `{seam.get('failures')}`",
        f"- Total vertices: `{seam.get('total_vertices')}`",
        f"- Total triangles: `{seam.get('total_triangles')}`",
        "",
        "## What passed",
        "",
    ]
    for check in c_report.get("checks", []):
        lines.append(f"- {check};")
    lines.extend([
        "",
        "## What remains unproven",
        "",
        "- official Transvoxel.cpp byte/table identity;",
        "- official class ID mapping;",
        "- official triangle topology equivalence;",
        "- Godot validation through the selectable M4 backend;",
        "- decision to make M4 the default backend.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m6/run_m6.py"]),
        run_step([sys.executable, "research/official_topology/m7/test_backend_switch_c.py"]),
    ]
    m6_report = read_json(M6_REPORT)
    c_report = read_json(C_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m6_report.get("status") == "PASS_M6_M4_C_SEAM_VALIDATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and c_report.get("status") == "PASS_M7_ZIG_NORMAL_API_BACKEND_SWITCH"
    )
    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.official_topology.m7.report.v1",
        "status": (
            "PASS_M7_NORMAL_API_M4_BACKEND_SWITCH_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M7_NORMAL_API_M4_BACKEND_SWITCH"
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "steps": steps,
        "outputs": {
            "c_validation": str(C_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m6_status": m6_report.get("status"),
        "c_validation": c_report,
    }
    M7_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, c_report)
    print()
    print("M7:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
