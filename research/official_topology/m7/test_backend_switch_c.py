#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run M7 backend-switch validation with Zig."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M7_DIR = ROOT / "research" / "official_topology" / "m7"
REPORT_PATH = M7_DIR / "m7_c_validation.json"

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
    if source == "cache":
        return "configured-zig"
    if isinstance(source, str) and source.startswith("auto-search:"):
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
        "examples/c_m7_backend_switch/main.c",
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
            out.append("<temp>/m7_backend_switch.exe")
        else:
            out.append(item)
    return out


def parse_key_values(line: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for key, value in re.findall(r"([a-zA-Z0-9_]+)=(-?\d+)", line):
        result[key] = int(value)
    return result


def parse_stdout(stdout: str) -> Dict[str, Any]:
    switch_line = ""
    seam_line = ""
    for line in stdout.splitlines():
        if line.startswith("m7 backend switch "):
            switch_line = line
        elif line.startswith("m7 normal_api_m4_seams "):
            seam_line = line
    return {
        "switch_line": switch_line,
        "seam_line": seam_line,
        "switch": parse_key_values(switch_line),
        "seam": parse_key_values(seam_line),
    }


def parsed_output_is_valid(parsed: Dict[str, Any]) -> List[str]:
    errors = []
    switch = parsed["switch"]
    seam = parsed["seam"]
    required_switch = {
        "cases": 512,
        "default_vertices": 10496,
        "default_triangles": 12288,
        "m4_vertices": 4096,
        "m4_triangles": 2640,
        "count_differences": 510,
        "restored_default": 1,
    }
    for key, expected in required_switch.items():
        if switch.get(key) != expected:
            errors.append(f"switch {key} expected {expected}, got {switch.get(key)}")
    required_seam = {
        "fields": 7,
        "seeds": 12,
        "grid": 8,
        "builds": 5376,
        "shared_faces": 9408,
        "failures": 0,
        "total_vertices": 14909,
        "total_triangles": 9503,
    }
    for key, expected in required_seam.items():
        if seam.get(key) != expected:
            errors.append(f"seam {key} expected {expected}, got {seam.get(key)}")
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

    with tempfile.TemporaryDirectory(prefix="transvoxel_m7_zig_") as tmp:
        exe = Path(tmp) / ("m7_backend_switch.exe" if sys.platform.startswith("win") else "m7_backend_switch")
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
            "schema": "boqsc.transvoxel.official_topology.m7.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": "Zig is required for M7 backend-switch validation.",
            "attempts": [],
        }
        write_json(REPORT_PATH, report)
        print("M7 C backend-switch validation:", report["status"])
        return 1

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            parsed = result["parsed"]
            report = {
                "schema": "boqsc.transvoxel.official_topology.m7.c_validation.v1",
                "status": "PASS_M7_ZIG_NORMAL_API_BACKEND_SWITCH",
                "ok": True,
                "compiler": result["candidate"],
                "source": result["source"],
                "validated_files": [
                    "include/transvoxel.h",
                    "include/transvoxel_m4_backend.h",
                    "include/transvoxel_m4_candidate.h",
                    "src/transvoxel.c",
                    "src/transvoxel_m4_backend.c",
                    "src/transvoxel_m4_candidate.c",
                    "examples/c_m7_backend_switch/main.c",
                ],
                "checks": [
                    "compiled with Zig C99",
                    "normal API default backend builds all 512 cases",
                    "M4 backend installs into normal tv_build_transition_cell API",
                    "normal API with M4 installed matches M4 generated counts for all 512 cases",
                    "normal API with M4 installed passes deterministic strip seam validation",
                    "M4 backend uninstalls and restores default backend totals",
                    "default backend and M4 backend remain structurally distinct",
                ],
                "switch": parsed["switch"],
                "seam": parsed["seam"],
                "stdout": result["stdout"],
                "attempts": attempts,
            }
            write_json(REPORT_PATH, report)
            print("M7 C backend-switch validation:", report["status"])
            print(result["stdout"])
            return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m7.c_validation.v1",
        "status": "FAIL_M7_ZIG_NORMAL_API_BACKEND_SWITCH",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M7 C backend-switch validation:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
