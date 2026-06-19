#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run the M20 regular-cell C proof with Zig."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M20_DIR = ROOT / "research" / "official_topology" / "m20"
REPORT = M20_DIR / "m20_c_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

EXPECTED = {
    "cases": 256,
    "vertices": 1536,
    "triangles": 820,
    "max_vertices": 12,
    "max_triangles": 5,
    "small_buffer_checks": 508,
    "failures": 0,
}


def write_json(data: Dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse(stdout: str) -> Dict[str, int]:
    for line in stdout.splitlines():
        if line.startswith("m20 regular "):
            return {
                key: int(value)
                for key, value in re.findall(
                    r"([a-zA-Z0-9_]+)=(-?\d+)",
                    line,
                )
            }
    return {}


def main() -> int:
    candidates = [
        candidate
        for candidate in test_core_c.compiler_candidates()
        if candidate.get("kind") == "zig"
    ]
    attempts: List[Dict[str, Any]] = []
    for candidate in candidates:
        _, error = test_core_c._resolve_executable(candidate["args"])
        if error:
            attempts.append({
                "status": "SKIP_UNRESOLVED_COMPILER",
                "error": error,
            })
            continue
        with tempfile.TemporaryDirectory(prefix="transvoxel_m20_") as tmp:
            exe = Path(tmp) / (
                "m20_regular.exe"
                if sys.platform.startswith("win")
                else "m20_regular"
            )
            command = list(candidate["args"]) + [
                "-std=c99",
                "-Wall",
                "-Wextra",
                "-pedantic",
                "-Iinclude",
                "-Igenerated",
                "src/transvoxel.c",
                "examples/c_m20_regular_cell/main.c",
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
                attempts.append({
                    "status": "FAIL_COMPILE",
                    "returncode": compile_proc.returncode,
                    "stdout": compile_proc.stdout[-4000:],
                    "stderr": compile_proc.stderr[-4000:],
                })
                continue
            run_proc = subprocess.run(
                [str(exe)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            metrics = parse(run_proc.stdout)
            errors = [
                f"{key} expected {expected}, got {metrics.get(key)}"
                for key, expected in EXPECTED.items()
                if metrics.get(key) != expected
            ]
            attempt = {
                "status": (
                    "PASS"
                    if run_proc.returncode == 0 and not errors
                    else "FAIL_RUN"
                ),
                "returncode": run_proc.returncode,
                "stdout": run_proc.stdout.strip(),
                "stderr": run_proc.stderr[-4000:],
                "metrics": metrics,
                "errors": errors,
            }
            attempts.append(attempt)
            if attempt["status"] == "PASS":
                report = {
                    "schema": (
                        "boqsc.transvoxel.official_topology."
                        "m20.c_validation.v1"
                    ),
                    "status": (
                        "PASS_M20_ZIG_CLEAN_ROOM_REGULAR_CELL_RUNTIME"
                    ),
                    "ok": True,
                    "compiler": "zig cc",
                    "checks": [
                        "all 256 regular cases through public C API",
                        "table counts and case indexes",
                        "active-edge interpolation",
                        "triangle index validity",
                        "small vertex and triangle buffers",
                    ],
                    "metrics": metrics,
                    "attempts": attempts,
                }
                write_json(report)
                print("M20 C regular:", report["status"])
                print(run_proc.stdout.strip())
                return 0
    report = {
        "schema": "boqsc.transvoxel.official_topology.m20.c_validation.v1",
        "status": (
            "FAIL_MISSING_ZIG"
            if not candidates
            else "FAIL_M20_ZIG_CLEAN_ROOM_REGULAR_CELL_RUNTIME"
        ),
        "ok": False,
        "attempts": attempts,
    }
    write_json(report)
    print("M20 C regular:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
