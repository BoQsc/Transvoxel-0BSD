#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run M6 C seam validation for the opt-in M4 backend."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M6_DIR = ROOT / "research" / "official_topology" / "m6"
REPORT_PATH = M6_DIR / "m6_c_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def zig_candidates() -> List[Dict[str, Any]]:
    return [
        candidate
        for candidate in test_core_c.compiler_candidates()
        if candidate.get("kind") == "zig"
    ]


def stable_compiler_label(candidate: Dict[str, Any]) -> str:
    return "zig cc" if candidate.get("kind") == "zig" else test_core_c._compiler_label(candidate)


def stable_source(candidate: Dict[str, Any]) -> Any:
    source = candidate.get("source")
    if isinstance(source, str) and source.startswith("auto-search:"):
        return "auto-search"
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
        "examples/c_m6_m4_seams/main.c",
        "-o",
        str(exe),
    ]


def stable_command(command: List[str], exe: Path, candidate: Dict[str, Any]) -> List[str]:
    out = []
    exe_text = str(exe)
    for index, item in enumerate(command):
        if index == 0 and candidate.get("kind") == "zig":
            out.append("zig")
        elif item == exe_text:
            out.append("<temp>/m6_m4_seams.exe")
        else:
            out.append(item)
    return out


def parse_key_values(line: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for key, value in re.findall(r"([a-zA-Z0-9_]+)=(-?\d+)", line):
        result[key] = int(value)
    return result


def parse_stdout(stdout: str) -> Dict[str, Any]:
    seam_line = ""
    comparison_line = ""
    for line in stdout.splitlines():
        if line.startswith("m6 m4 seams "):
            seam_line = line
        elif line.startswith("m6 default comparison "):
            comparison_line = line
    return {
        "seam_line": seam_line,
        "comparison_line": comparison_line,
        "seam": parse_key_values(seam_line),
        "comparison": parse_key_values(comparison_line),
    }


def parsed_output_is_valid(parsed: Dict[str, Any]) -> List[str]:
    errors = []
    seam = parsed["seam"]
    comparison = parsed["comparison"]
    required_seam = {
        "fields": 7,
        "seeds": 12,
        "grid": 8,
        "builds": 5376,
        "shared_faces": 9408,
        "failures": 0,
    }
    for key, expected in required_seam.items():
        if seam.get(key) != expected:
            errors.append(f"seam {key} expected {expected}, got {seam.get(key)}")
    if seam.get("total_triangles", 0) <= 0:
        errors.append("seam total_triangles must be positive")
    if seam.get("total_vertices", 0) <= 0:
        errors.append("seam total_vertices must be positive")

    required_comparison = {
        "cases": 512,
        "default_failures": 0,
        "m4_failures": 0,
        "m4_triangles": 2640,
        "structurally_distinct": 1,
    }
    for key, expected in required_comparison.items():
        if comparison.get(key) != expected:
            errors.append(f"comparison {key} expected {expected}, got {comparison.get(key)}")
    if comparison.get("count_differences", 0) <= 0:
        errors.append("comparison count_differences must be positive")
    if comparison.get("default_triangles", 0) <= comparison.get("m4_triangles", 0):
        errors.append("default backend should remain structurally larger than M4 candidate in this diagnostic")
    return errors


def try_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    exe_path, resolve_error = test_core_c._resolve_executable(candidate["args"])
    label = stable_compiler_label(candidate)
    source = stable_source(candidate)
    if resolve_error:
        return {
            "candidate": label,
            "source": source,
            "status": "SKIP_UNRESOLVED_COMPILER",
            "error": resolve_error,
        }

    with tempfile.TemporaryDirectory(prefix="transvoxel_m6_zig_") as tmp:
        exe = Path(tmp) / ("m6_m4_seams.exe" if sys.platform.startswith("win") else "m6_m4_seams")
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
                "candidate": label,
                "source": source,
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
        output_errors = parsed_output_is_valid(parsed)
        if run_proc.returncode != 0 or output_errors:
            return {
                "candidate": label,
                "source": source,
                "resolved_executable": "<zig>",
                "status": "FAIL_RUN",
                "command": stable_command(command, exe, candidate),
                "returncode": run_proc.returncode,
                "stdout": run_proc.stdout[-4000:],
                "stderr": run_proc.stderr[-4000:],
                "output_errors": output_errors,
                "parsed": parsed,
            }

        return {
            "candidate": label,
            "source": source,
            "resolved_executable": "<zig>",
            "status": "PASS",
            "command": stable_command(command, exe, candidate),
            "stdout": run_proc.stdout.strip(),
            "stderr": run_proc.stderr.strip(),
            "returncode": run_proc.returncode,
            "parsed": parsed,
        }


def main() -> int:
    attempts = []
    candidates = zig_candidates()
    if not candidates:
        report = {
            "schema": "boqsc.transvoxel.official_topology.m6.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": "Zig is required for M6 seam validation.",
            "attempts": [],
        }
        write_json(REPORT_PATH, report)
        print("M6 C seam validation:", report["status"])
        return 1

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            parsed = result["parsed"]
            report = {
                "schema": "boqsc.transvoxel.official_topology.m6.c_validation.v1",
                "status": "PASS_M6_ZIG_M4_SEAM_VALIDATION",
                "ok": True,
                "compiler": result["candidate"],
                "source": result["source"],
                "validated_files": [
                    "include/transvoxel_m4_candidate.h",
                    "src/transvoxel_m4_candidate.c",
                    "src/transvoxel.c",
                    "examples/c_m6_m4_seams/main.c",
                ],
                "checks": [
                    "compiled with Zig C99",
                    "built M4 candidate transition cells across deterministic strips",
                    "compared shared side-face fingerprints",
                    "verified zero strip seam mismatches",
                    "built default transition backend for all 512 cases",
                    "confirmed M4 candidate is structurally distinct from default backend",
                ],
                "seam": parsed["seam"],
                "comparison": parsed["comparison"],
                "stdout": result["stdout"],
                "attempts": attempts,
            }
            write_json(REPORT_PATH, report)
            print("M6 C seam validation:", report["status"])
            print(result["stdout"])
            return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m6.c_validation.v1",
        "status": "FAIL_M6_ZIG_M4_SEAM_VALIDATION",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M6 C seam validation:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
