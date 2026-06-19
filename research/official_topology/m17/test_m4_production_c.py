#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run the M17 combined M4 production C assembler with Zig."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M17_DIR = ROOT / "research" / "official_topology" / "m17"
REPORT_PATH = M17_DIR / "m17_c_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

EXPECTED = {
    "normal_cases": 512,
    "normal_vertices": 4096,
    "normal_triangles": 2640,
    "mapped_builds": 672,
    "mapped_vertices": 2372,
    "mapped_triangles": 1464,
    "backend_installed": 1,
    "restored_default": 1,
    "failures": 0,
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
        "src/transvoxel_m4_backend.c",
        "examples/c_m17_m4_production/main.c",
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
            out.append("<temp>/m17_m4_production.exe")
        else:
            out.append(item)
    return out


def parse_stdout(stdout: str) -> Dict[str, int]:
    for line in stdout.splitlines():
        if line.startswith("m17 production "):
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
    with tempfile.TemporaryDirectory(prefix="transvoxel_m17_zig_") as tmp:
        exe = Path(tmp) / (
            "m17_m4_production.exe"
            if sys.platform.startswith("win")
            else "m17_m4_production"
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
    attempts: List[Dict[str, Any]] = []
    candidates = zig_candidates()
    if not candidates:
        report = {
            "schema": "boqsc.transvoxel.official_topology.m17.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": "Zig is required for M17 M4 production C validation.",
            "attempts": [],
        }
        write_json(REPORT_PATH, report)
        print("M17 C production:", report["status"])
        return 1

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            report = {
                "schema": "boqsc.transvoxel.official_topology.m17.c_validation.v1",
                "status": "PASS_M17_ZIG_M4_SELECTED_PRODUCTION_ASSEMBLER",
                "ok": True,
                "compiler": result["candidate"],
                "source": result["source"],
                "checks": [
                    "installed M4 through the normal transvoxel.h backend hook",
                    "built all 512 cases through tv_build_transition_cell",
                    "built mapped edge/corner cells in the same process",
                    "validated every produced triangle",
                    "uninstalled M4 and restored the independent default backend",
                ],
                "metrics": result["parsed"],
                "stdout": result["stdout"],
                "attempts": attempts,
            }
            write_json(REPORT_PATH, report)
            print("M17 C production:", report["status"])
            print(result["stdout"])
            return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m17.c_validation.v1",
        "status": "FAIL_M17_ZIG_M4_SELECTED_PRODUCTION_ASSEMBLER",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M17 C production:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
