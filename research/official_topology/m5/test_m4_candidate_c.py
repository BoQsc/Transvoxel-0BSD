#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run the opt-in M4 candidate C builder with Zig."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[3]
M5_DIR = ROOT / "research" / "official_topology" / "m5"
REPORT_PATH = M5_DIR / "m5_c_validation.json"

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


def compile_command(candidate: Dict[str, Any], exe: Path) -> List[str]:
    return list(candidate["args"]) + [
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-Iinclude",
        "-Igenerated",
        "src/transvoxel_m4_candidate.c",
        "examples/c_m4_candidate/main.c",
        "-o",
        str(exe),
    ]


def stable_compiler_label(candidate: Dict[str, Any]) -> str:
    if candidate.get("kind") == "zig":
        return "zig cc"
    return test_core_c._compiler_label(candidate)


def stable_source(candidate: Dict[str, Any]) -> Any:
    source = candidate.get("source")
    if isinstance(source, str) and source.startswith("auto-search:"):
        return "auto-search"
    return source


def stable_command(command: List[str], exe: Path, candidate: Dict[str, Any]) -> List[str]:
    exe_text = str(exe)
    result = []
    for index, item in enumerate(command):
        if index == 0 and candidate.get("kind") == "zig":
            result.append("zig")
        elif item == exe_text:
            result.append("<temp>/m4_candidate.exe")
        else:
            result.append(item)
    return result


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

    with tempfile.TemporaryDirectory(prefix="transvoxel_m5_zig_") as tmp:
        exe = Path(tmp) / ("m4_candidate.exe" if sys.platform.startswith("win") else "m4_candidate")
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
                "resolved_executable": "<zig>" if candidate.get("kind") == "zig" else exe_path,
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
        stdout = run_proc.stdout.strip()
        expected_tokens = [
            "m4 candidate exhaustive cases=512",
            "vertices=4096",
            "triangles=2640",
            "max_vertices=12",
            "max_triangles=12",
        ]
        missing = [token for token in expected_tokens if token not in stdout]
        if run_proc.returncode != 0 or missing:
            return {
                "candidate": label,
                "source": source,
                "resolved_executable": "<zig>" if candidate.get("kind") == "zig" else exe_path,
                "status": "FAIL_RUN",
                "command": stable_command(command, exe, candidate),
                "returncode": run_proc.returncode,
                "stdout": run_proc.stdout[-4000:],
                "stderr": run_proc.stderr[-4000:],
                "missing_stdout_tokens": missing,
            }

        return {
            "candidate": label,
            "source": source,
            "resolved_executable": "<zig>" if candidate.get("kind") == "zig" else exe_path,
            "status": "PASS",
            "command": stable_command(command, exe, candidate),
            "stdout": stdout,
            "stderr": run_proc.stderr.strip(),
            "returncode": run_proc.returncode,
        }


def main() -> int:
    attempts = []
    candidates = zig_candidates()
    if not candidates:
        report = {
            "schema": "boqsc.transvoxel.official_topology.m5.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": (
                "Zig is required for M5. Put zig.exe in zig_path.txt or "
                "c_compiler_path.txt, or set ZIG_EXE."
            ),
            "attempts": [],
        }
        write_json(REPORT_PATH, report)
        print("M5 C validation:", report["status"])
        print(report["reason"])
        return 1

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            report = {
                "schema": "boqsc.transvoxel.official_topology.m5.c_validation.v1",
                "status": "PASS_M5_ZIG_CANDIDATE_BUILDER",
                "ok": True,
                "compiler": result["candidate"],
                "source": result.get("source"),
                "validated_files": [
                    "include/transvoxel_m4_candidate.h",
                    "src/transvoxel_m4_candidate.c",
                    "generated/official_topology_candidate_tables.h",
                    "examples/c_m4_candidate/main.c",
                ],
                "checks": [
                    "compiled with Zig C99",
                    "built all 512 M4 transition cases",
                    "matched generated per-case vertex and triangle counts",
                    "verified generated vertex pairs cross signs",
                    "verified emitted vertex interpolation positions",
                    "verified emitted triangle indices and table copies",
                    "verified small vertex/triangle buffer error handling",
                ],
                "stdout": result["stdout"],
                "attempts": attempts,
            }
            write_json(REPORT_PATH, report)
            print("M5 C validation:", report["status"])
            print(result["stdout"])
            return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m5.c_validation.v1",
        "status": "FAIL_M5_ZIG_CANDIDATE_BUILDER",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M5 C validation:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
