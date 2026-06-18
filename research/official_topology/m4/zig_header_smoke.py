#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile a tiny C smoke test for the generated M4 header using Zig.

This is intentionally optional for M4. If Zig is not configured, the script
reports SKIP_MISSING_ZIG and exits successfully. If Zig is present and the
header does not compile, the script fails.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = ROOT / "research" / "official_topology" / "m4" / "zig_header_smoke.json"
HEADER_PATH = ROOT / "generated" / "official_topology_candidate_tables.h"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402


def write_report(report: Dict[str, Any]) -> None:
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def zig_candidates() -> List[Dict[str, Any]]:
    return [
        candidate
        for candidate in test_core_c.compiler_candidates()
        if candidate.get("kind") == "zig"
    ]


def resolved_candidate() -> Optional[Dict[str, Any]]:
    for candidate in zig_candidates():
        exe, error = test_core_c._resolve_executable(candidate["args"])
        if error:
            continue
        result = dict(candidate)
        result["resolved_executable"] = exe
        return result
    return None


def smoke_source() -> str:
    return r'''
#include <stdint.h>
#include "generated/official_topology_candidate_tables.h"

typedef char assert_case_count[(OTC_M4_CASE_COUNT == 512u) ? 1 : -1];
typedef char assert_class_count[(OTC_M4_RESEARCH_CLASS_COUNT == 73u) ? 1 : -1];
typedef char assert_sample_count[(OTC_M4_SAMPLE_COUNT == 13u) ? 1 : -1];
typedef char assert_vertex_pair_count[
    ((sizeof(otc_m4_vertex_pairs) / sizeof(otc_m4_vertex_pairs[0]))
    == OTC_M4_VERTEX_PAIR_COUNT) ? 1 : -1
];
typedef char assert_triangle_count[
    ((sizeof(otc_m4_triangles) / sizeof(otc_m4_triangles[0]))
    == OTC_M4_TRIANGLE_COUNT) ? 1 : -1
];

int main(void) {
    uint32_t sum = 0;
    sum += otc_m4_case_research_class[0];
    sum += otc_m4_case_research_class[511];
    sum += otc_m4_case_triangle_count[1];
    sum += otc_m4_vertex_pairs[0][0];
    sum += otc_m4_triangles[0][0];
    return (sum > 255u) ? 1 : 0;
}
'''.lstrip()


def stable_compiler_label(candidate: Dict[str, Any]) -> str:
    if candidate.get("kind") == "zig":
        return "zig cc"
    return test_core_c._compiler_label(candidate)


def stable_command(
    command: List[str],
    source: Path,
    exe: Path,
    candidate: Dict[str, Any],
) -> List[str]:
    result = []
    source_text = str(source)
    exe_text = str(exe)
    for index, item in enumerate(command):
        if index == 0 and candidate.get("kind") == "zig":
            result.append("zig")
        elif item == source_text:
            result.append("<temp>/m4_header_smoke.c")
        elif item == exe_text:
            result.append("<temp>/m4_header_smoke.exe")
        else:
            result.append(item)
    return result


def main() -> int:
    if not HEADER_PATH.exists():
        report = {
            "schema": "boqsc.transvoxel.official_topology.m4.zig_header_smoke.v1",
            "status": "FAIL_MISSING_HEADER",
            "ok": False,
            "header": str(HEADER_PATH.relative_to(ROOT)),
            "errors": ["generated M4 header does not exist"],
        }
        write_report(report)
        print("M4 Zig header smoke:", report["status"])
        return 1

    candidate = resolved_candidate()
    if candidate is None:
        report = {
            "schema": "boqsc.transvoxel.official_topology.m4.zig_header_smoke.v1",
            "status": "SKIP_MISSING_ZIG",
            "ok": None,
            "header": str(HEADER_PATH.relative_to(ROOT)),
            "reason": (
                "Zig was not found. Put zig.exe in zig_path.txt or "
                "c_compiler_path.txt, or set ZIG_EXE."
            ),
        }
        write_report(report)
        print("M4 Zig header smoke:", report["status"])
        print(report["reason"])
        return 0

    with tempfile.TemporaryDirectory(prefix="transvoxel_m4_zig_") as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / "m4_header_smoke.c"
        exe = tmp_dir / ("m4_header_smoke.exe" if sys.platform.startswith("win") else "m4_header_smoke")
        source.write_text(smoke_source(), encoding="utf-8")
        command = list(candidate["args"]) + [
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-I.",
            str(source),
            "-o",
            str(exe),
        ]
        compile_proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if compile_proc.returncode != 0:
            report = {
                "schema": "boqsc.transvoxel.official_topology.m4.zig_header_smoke.v1",
                "status": "FAIL_ZIG_HEADER_COMPILE",
                "ok": False,
                "header": str(HEADER_PATH.relative_to(ROOT)),
                "compiler": stable_compiler_label(candidate),
                "command": stable_command(command, source, exe, candidate),
                "stdout": compile_proc.stdout[-4000:],
                "stderr": compile_proc.stderr[-4000:],
                "returncode": compile_proc.returncode,
            }
            write_report(report)
            print("M4 Zig header smoke:", report["status"])
            print(report["stderr"])
            return 1
        run_proc = subprocess.run(
            [str(exe)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report = {
            "schema": "boqsc.transvoxel.official_topology.m4.zig_header_smoke.v1",
            "status": "PASS_ZIG_HEADER_SMOKE" if run_proc.returncode == 0 else "FAIL_ZIG_HEADER_RUN",
            "ok": run_proc.returncode == 0,
            "header": str(HEADER_PATH.relative_to(ROOT)),
            "compiler": stable_compiler_label(candidate),
            "command": stable_command(command, source, exe, candidate),
            "stdout": run_proc.stdout[-4000:],
            "stderr": run_proc.stderr[-4000:],
            "returncode": run_proc.returncode,
        }
        write_report(report)
        print("M4 Zig header smoke:", report["status"])
        if run_proc.returncode != 0:
            print(report["stderr"])
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
