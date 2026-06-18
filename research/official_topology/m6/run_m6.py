#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M6: seam/chunk validation for the opt-in M4 C backend."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
M6_DIR = ROOT / "research" / "official_topology" / "m6"
M5_REPORT = ROOT / "research" / "official_topology" / "m5" / "m5_report.json"
C_REPORT = M6_DIR / "m6_c_validation.json"
M6_REPORT = M6_DIR / "m6_report.json"
RESULTS = M6_DIR / "results.md"


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
    seam = c_report.get("seam", {})
    comparison = c_report.get("comparison", {})
    lines = [
        "# M6 M4 Candidate Seam Validation",
        "",
        "M6 validates the opt-in M4 C backend across deterministic transition-cell strips.",
        "",
        f"- Status: `{report['status']}`",
        f"- C validation: `{c_report['status']}`",
        f"- Compiler: `{c_report.get('compiler', 'NOT_AVAILABLE')}`",
        f"- Strip fields: `{seam.get('fields')}`",
        f"- Seeds per field: `{seam.get('seeds')}`",
        f"- Grid size: `{seam.get('grid')} x {seam.get('grid')}`",
        f"- M4 strip builds: `{seam.get('builds')}`",
        f"- Shared faces checked: `{seam.get('shared_faces')}`",
        f"- Seam failures: `{seam.get('failures')}`",
        f"- M4 strip triangles: `{seam.get('total_triangles')}`",
        "",
        "## Default backend comparison",
        "",
        f"- Cases checked: `{comparison.get('cases')}`",
        f"- Default build failures: `{comparison.get('default_failures')}`",
        f"- M4 build failures: `{comparison.get('m4_failures')}`",
        f"- Count differences: `{comparison.get('count_differences')}`",
        f"- Default triangles: `{comparison.get('default_triangles')}`",
        f"- M4 triangles: `{comparison.get('m4_triangles')}`",
        f"- Structurally distinct: `{comparison.get('structurally_distinct')}`",
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
        "- Godot validation through the M4 candidate backend;",
        "- decision to replace the default transition backend.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m5/run_m5.py"]),
        run_step([sys.executable, "research/official_topology/m6/test_m4_seams_c.py"]),
    ]
    m5_report = read_json(M5_REPORT)
    c_report = read_json(C_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m5_report.get("status") == "PASS_M5_OPT_IN_C_RUNTIME_CANDIDATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and c_report.get("status") == "PASS_M6_ZIG_M4_SEAM_VALIDATION"
    )
    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.official_topology.m6.report.v1",
        "status": (
            "PASS_M6_M4_C_SEAM_VALIDATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M6_M4_C_SEAM_VALIDATION"
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
        "m5_status": m5_report.get("status"),
        "c_validation": c_report,
    }
    M6_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, c_report)
    print()
    print("M6:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
