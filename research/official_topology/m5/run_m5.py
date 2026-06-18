#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M5: opt-in C runtime integration for M4 candidate tables."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
M5_DIR = ROOT / "research" / "official_topology" / "m5"
M4_REPORT = ROOT / "research" / "official_topology" / "m4" / "m4_report.json"
C_REPORT = M5_DIR / "m5_c_validation.json"
M5_REPORT = M5_DIR / "m5_report.json"
RESULTS = M5_DIR / "results.md"


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
    lines = [
        "# M5 Opt-in C Runtime Candidate",
        "",
        "M5 adds an opt-in C builder for the M4 runtime candidate topology tables.",
        "",
        f"- Status: `{report['status']}`",
        f"- C validation: `{c_report['status']}`",
        f"- Compiler: `{c_report.get('compiler', 'NOT_AVAILABLE')}`",
        "",
        "## Added runtime path",
        "",
        "- `include/transvoxel_m4_candidate.h`",
        "- `src/transvoxel_m4_candidate.c`",
        "- `examples/c_m4_candidate/main.c`",
        "",
        "The default `tv_build_transition_cell()` path is unchanged. Engines must opt into M5 with `tv_m4_build_transition_cell_candidate()`.",
        "",
        "## Zig validation",
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
        "- Godot/runtime seam validation through the M4 candidate backend;",
        "- decision to replace the default transition backend.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m4/run_m4.py"]),
        run_step([sys.executable, "research/official_topology/m5/test_m4_candidate_c.py"]),
    ]
    m4_report = read_json(M4_REPORT)
    c_report = read_json(C_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m4_report.get("status") == "PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and c_report.get("status") == "PASS_M5_ZIG_CANDIDATE_BUILDER"
    )
    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.official_topology.m5.report.v1",
        "status": (
            "PASS_M5_OPT_IN_C_RUNTIME_CANDIDATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M5_OPT_IN_C_RUNTIME_CANDIDATE"
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
        "m4_status": m4_report.get("status"),
        "c_validation": c_report,
    }
    M5_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, c_report)
    print()
    print("M5:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
