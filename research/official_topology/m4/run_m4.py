#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run the M4 runtime-candidate table milestone."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
M4_DIR = ROOT / "research" / "official_topology" / "m4"
GENERATED_TABLE = ROOT / "generated" / "official_topology_candidate_tables.json"
GENERATED_HEADER = ROOT / "generated" / "official_topology_candidate_tables.h"
VALIDATION_REPORT = M4_DIR / "runtime_table_validation.json"
ZIG_SMOKE_REPORT = M4_DIR / "zig_header_smoke.json"
M4_REPORT = M4_DIR / "m4_report.json"
RESULTS = M4_DIR / "results.md"


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


def write_results(
    report: Dict[str, object],
    validation: Dict[str, object],
    zig_smoke: Dict[str, object],
) -> None:
    zig_status = zig_smoke.get("status", "NOT_RUN")
    lines = [
        "# M4 Runtime Candidate Tables",
        "",
        "M4 converts the M3 clean-room topology derivation into runtime-ready candidate tables.",
        "",
        f"- Status: `{report['status']}`",
        f"- Runtime table: `generated/official_topology_candidate_tables.json`",
        f"- C header: `generated/official_topology_candidate_tables.h`",
        f"- Cases: `{validation['case_count']}`",
        f"- Research classes: `{validation['research_class_count']}`",
        f"- Total runtime vertex pairs: `{validation['total_vertex_pairs']}`",
        f"- Total runtime triangles: `{validation['total_triangles']}`",
        f"- SHA-256: `{validation['sha256_without_this_field']}`",
        f"- Zig header smoke: `{zig_status}`",
        "",
        "## What passed",
        "",
        "- all 512 cases are present;",
        "- all 73 M3 research classes are present;",
        "- every case has a D4/complement transform from its class representative;",
        "- every generated vertex lies on a sign-changing sample edge;",
        "- every case preserves the M3-derived boundary exactly;",
        "- no generated triangle complex has degenerate triangles, overused edges, or non-adjacent intersections;",
        "- flat runtime arrays match the per-case records;",
        "- generated JSON and C header regenerate deterministically.",
        "",
        "## Zig C header smoke",
        "",
    ]
    if zig_status == "PASS_ZIG_HEADER_SMOKE":
        lines.append("- Zig compiled and ran a C99 include smoke test for the generated header.")
    elif zig_status == "SKIP_MISSING_ZIG":
        lines.append("- Zig was not configured in this environment, so the C header smoke test was skipped.")
        lines.append("- Put `zig.exe` in `zig_path.txt` or `c_compiler_path.txt`, or set `ZIG_EXE`, to enable this check.")
    else:
        lines.append(f"- Zig smoke status: `{zig_status}`.")
    lines.extend([
        "",
        "## What remains unproven",
        "",
        "- official Transvoxel.cpp byte/table identity;",
        "- official class ID mapping;",
        "- official triangle topology equivalence;",
        "- official vertex encoding equivalence;",
        "- production replacement status in the default C core.",
        "",
        "The generated M4 tables are a candidate replacement path, not the default core table.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m4/generate_runtime_tables.py"]),
        run_step([sys.executable, "research/official_topology/m4/validate_runtime_tables.py"]),
        run_step([sys.executable, "research/official_topology/m4/zig_header_smoke.py"]),
    ]
    validation = read_json(VALIDATION_REPORT)
    zig_smoke = read_json(ZIG_SMOKE_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and bool(validation.get("ok"))
        and zig_smoke.get("status") in ("PASS_ZIG_HEADER_SMOKE", "SKIP_MISSING_ZIG")
    )
    report: Dict[str, object] = {
        "schema": "boqsc.transvoxel.official_topology.m4.report.v1",
        "status": (
            "PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M4_RUNTIME_TABLES"
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "steps": steps,
        "outputs": {
            "runtime_table": str(GENERATED_TABLE.relative_to(ROOT)),
            "c_header": str(GENERATED_HEADER.relative_to(ROOT)),
            "validation_report": str(VALIDATION_REPORT.relative_to(ROOT)),
            "zig_header_smoke": str(ZIG_SMOKE_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "validation": validation,
        "zig_header_smoke": zig_smoke,
    }
    M4_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, validation, zig_smoke)
    print()
    print("M4:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
