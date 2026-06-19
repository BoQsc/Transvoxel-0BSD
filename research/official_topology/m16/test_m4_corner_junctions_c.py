#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run M16 M4 deformed corner-junction validation with Zig."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M16_DIR = ROOT / "research" / "official_topology" / "m16"
REPORT_PATH = M16_DIR / "m16_c_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

EXPECTED = {
    "octants": 8,
    "fields": 7,
    "seeds": 8,
    "junctions": 448,
    "builds": 1344,
    "vertices": 4680,
    "triangles": 2896,
    "invalid_triangles": 0,
    "degenerate_triangles": 0,
    "internal_winding_failures": 0,
    "shared_faces": 1344,
    "nonempty_shared_faces": 500,
    "shared_samples": 6720,
    "sample_position_failures": 0,
    "sample_value_failures": 0,
    "lateral_geometry_failures": 0,
    "lateral_winding_failures": 0,
    "corner_position_failures": 0,
    "corner_value_failures": 0,
}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def zig_candidates() -> List[Dict[str, Any]]:
    return [
        candidate
        for candidate in test_core_c.compiler_candidates()
        if candidate.get("kind") == "zig"
    ]


def stable_source(candidate: Dict[str, Any]) -> Any:
    source = candidate.get("source")
    if source == "cache" or (
        isinstance(source, str) and source.startswith("auto-search:")
    ):
        return "configured-zig"
    return source


def compile_command(candidate: Dict[str, Any], exe: Path) -> List[str]:
    return list(candidate["args"]) + [
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-Iinclude",
        "-Igenerated",
        "src/transvoxel.c",
        "src/transvoxel_m4_candidate.c",
        "examples/c_m16_m4_corner_junctions/main.c",
        "-o",
        str(exe),
    ]


def stable_command(
    command: List[str],
    exe: Path,
    candidate: Dict[str, Any],
) -> List[str]:
    out: List[str] = []
    for index, item in enumerate(command):
        if index == 0 and candidate.get("kind") == "zig":
            out.append("zig")
        elif item == str(exe):
            out.append("<temp>/m16_m4_corner_junctions.exe")
        else:
            out.append(item)
    return out


def parse_stdout(stdout: str) -> Dict[str, int]:
    for line in stdout.splitlines():
        if line.startswith("m16 junctions "):
            return {
                key: int(value)
                for key, value in re.findall(
                    r"([a-zA-Z0-9_]+)=(-?\d+)",
                    line,
                )
            }
    return {}


def output_errors(parsed: Dict[str, int]) -> List[str]:
    return [
        f"{key} expected {expected}, got {parsed.get(key)}"
        for key, expected in EXPECTED.items()
        if parsed.get(key) != expected
    ]


def try_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    _, resolve_error = test_core_c._resolve_executable(candidate["args"])
    if resolve_error:
        return {
            "candidate": "zig cc",
            "source": stable_source(candidate),
            "status": "SKIP_UNRESOLVED_COMPILER",
            "error": resolve_error,
        }
    with tempfile.TemporaryDirectory(prefix="transvoxel_m16_zig_") as tmp:
        exe = Path(tmp) / (
            "m16_m4_corner_junctions.exe"
            if sys.platform.startswith("win")
            else "m16_m4_corner_junctions"
        )
        command = compile_command(candidate, exe)
        compile_proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if compile_proc.returncode != 0:
            return {
                "candidate": "zig cc",
                "source": stable_source(candidate),
                "resolved_executable": "<zig>",
                "status": "FAIL_COMPILE",
                "command": stable_command(command, exe, candidate),
                "returncode": compile_proc.returncode,
                "stdout": compile_proc.stdout[-4000:],
                "stderr": compile_proc.stderr[-4000:],
            }
        run_proc = subprocess.run(
            [str(exe)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        parsed = parse_stdout(run_proc.stdout)
        errors = output_errors(parsed)
        if run_proc.returncode != 0 or errors:
            return {
                "candidate": "zig cc",
                "source": stable_source(candidate),
                "resolved_executable": "<zig>",
                "status": "FAIL_RUN",
                "command": stable_command(command, exe, candidate),
                "returncode": run_proc.returncode,
                "stdout": run_proc.stdout[-8000:],
                "stderr": run_proc.stderr[-4000:],
                "output_errors": errors,
                "parsed": parsed,
            }
        return {
            "candidate": "zig cc",
            "source": stable_source(candidate),
            "resolved_executable": "<zig>",
            "status": "PASS",
            "command": stable_command(command, exe, candidate),
            "returncode": run_proc.returncode,
            "stdout": run_proc.stdout.strip(),
            "stderr": run_proc.stderr.strip(),
            "parsed": parsed,
        }


def main() -> int:
    candidates = zig_candidates()
    attempts: List[Dict[str, Any]] = []
    if not candidates:
        report = {
            "schema": "boqsc.transvoxel.official_topology.m16.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": "Zig is required for M16 corner-junction C validation.",
            "attempts": [],
        }
        write_json(REPORT_PATH, report)
        print("M16 C corner junctions:", report["status"])
        return 1

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            report = {
                "schema": "boqsc.transvoxel.official_topology.m16.c_validation.v1",
                "status": "PASS_M16_ZIG_M4_DEFORMED_CORNER_JUNCTIONS",
                "ok": True,
                "compiler": result["candidate"],
                "source": result["source"],
                "validated_files": [
                    "generated/official_topology_candidate_tables.h",
                    "include/transvoxel_m4_candidate.h",
                    "src/transvoxel_m4_candidate.c",
                    "examples/c_m16_m4_corner_junctions/main.c",
                ],
                "checks": [
                    "compiled mapped/deformed M4 transition cells with Zig C99",
                    "validated all eight block-corner octants",
                    "validated three perpendicular transition cells per junction",
                    "validated coincident lateral-face sample positions and values",
                    "validated matching lateral boundary edges with opposite winding",
                    "validated coherent internal triangle winding",
                    "validated shared inner corner positions and values",
                ],
                "metrics": result["parsed"],
                "stdout": result["stdout"],
                "attempts": attempts,
            }
            write_json(REPORT_PATH, report)
            print("M16 C corner junctions:", report["status"])
            print(result["stdout"])
            return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m16.c_validation.v1",
        "status": "FAIL_M16_ZIG_M4_DEFORMED_CORNER_JUNCTIONS",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M16 C corner junctions:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
