#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run the M18 reference-convention API proof with Zig."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M18_DIR = ROOT / "research" / "official_topology" / "m18"
REPORT_PATH = M18_DIR / "m18_c_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

EXPECTED = {
    "cases": 512,
    "mapping_checks": 512,
    "roundtrip_checks": 1024,
    "complement_checks": 512,
    "rotation_checks": 512,
    "build_checks": 512,
    "frame_checks": 6,
    "vertices": 4096,
    "triangles": 2640,
    "failures": 0,
}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        "examples/c_m18_reference_convention/main.c",
        "-o",
        str(exe),
    ]


def stable_command(
    command: List[str],
    exe: Path,
    candidate: Dict[str, Any],
) -> List[str]:
    return [
        (
            "zig"
            if index == 0 and candidate.get("kind") == "zig"
            else "<temp>/m18_reference_convention.exe"
            if item == str(exe)
            else item
        )
        for index, item in enumerate(command)
    ]


def parse_stdout(stdout: str) -> Dict[str, int]:
    for line in stdout.splitlines():
        if line.startswith("m18 reference "):
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
    if not candidates:
        report = {
            "schema": "boqsc.transvoxel.official_topology.m18.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": "Zig is required for M18 C validation.",
            "attempts": attempts,
        }
        write_json(REPORT_PATH, report)
        print("M18 C reference convention:", report["status"])
        return 1

    for candidate in candidates:
        _, resolve_error = test_core_c._resolve_executable(candidate["args"])
        if resolve_error:
            attempts.append({
                "candidate": "zig cc",
                "source": stable_source(candidate),
                "status": "SKIP_UNRESOLVED_COMPILER",
                "error": resolve_error,
            })
            continue
        with tempfile.TemporaryDirectory(prefix="transvoxel_m18_zig_") as tmp:
            exe = Path(tmp) / (
                "m18_reference_convention.exe"
                if sys.platform.startswith("win")
                else "m18_reference_convention"
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
                attempts.append({
                    "candidate": "zig cc",
                    "source": stable_source(candidate),
                    "status": "FAIL_COMPILE",
                    "command": stable_command(command, exe, candidate),
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
            parsed = parse_stdout(run_proc.stdout)
            output_errors = [
                f"{key} expected {expected}, got {parsed.get(key)}"
                for key, expected in EXPECTED.items()
                if parsed.get(key) != expected
            ]
            result = {
                "candidate": "zig cc",
                "source": stable_source(candidate),
                "status": (
                    "PASS"
                    if run_proc.returncode == 0 and not output_errors
                    else "FAIL_RUN"
                ),
                "command": stable_command(command, exe, candidate),
                "returncode": run_proc.returncode,
                "stdout": run_proc.stdout.strip(),
                "stderr": run_proc.stderr[-4000:],
                "parsed": parsed,
                "output_errors": output_errors,
            }
            attempts.append(result)
            if result["status"] == "PASS":
                report = {
                    "schema": (
                        "boqsc.transvoxel.official_topology."
                        "m18.c_validation.v1"
                    ),
                    "status": (
                        "PASS_M18_ZIG_PUBLISHED_REFERENCE_CONVENTION_API"
                    ),
                    "ok": True,
                    "compiler": "zig cc",
                    "source": result["source"],
                    "validated_files": [
                        "include/transvoxel_m4_candidate.h",
                        "src/transvoxel_m4_candidate.c",
                        "examples/c_m18_reference_convention/main.c",
                    ],
                    "checks": [
                        "all 512 local-to-published case-index mappings",
                        "all 512 published-to-local round trips",
                        "complement mapping",
                        "published 180-degree nibble property",
                        "all 512 M4 runtime builds remain unchanged",
                        "all six frame determinants are positive",
                    ],
                    "metrics": parsed,
                    "stdout": result["stdout"],
                    "attempts": attempts,
                }
                write_json(REPORT_PATH, report)
                print("M18 C reference convention:", report["status"])
                print(result["stdout"])
                return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m18.c_validation.v1",
        "status": "FAIL_M18_ZIG_PUBLISHED_REFERENCE_CONVENTION_API",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M18 C reference convention:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
