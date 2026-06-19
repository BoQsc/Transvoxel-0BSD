#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile an unchanged-style consumer against generated Transvoxel.cpp."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M25_DIR = ROOT / "research" / "official_topology" / "m25"
GENERATED = M25_DIR / "generated"
SOURCE = M25_DIR / "original_contract_consumer.cpp"
REPORT = M25_DIR / "m25_consumer_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402


def compiler_label(candidate: Dict[str, Any]) -> str:
    args = list(candidate.get("args", []))
    if candidate.get("kind") == "zig" and len(args) >= 2:
        return "zig c++"
    return " ".join(args)


def cpp_args(candidate: Dict[str, Any]) -> List[str] | None:
    args = list(candidate.get("args", []))
    if candidate.get("kind") == "zig":
        return [args[0], "c++"]
    executable = Path(args[0]).name.lower() if args else ""
    if executable in ("gcc", "gcc.exe", "cc", "cc.exe"):
        args[0] = str(Path(args[0]).with_name(
            "g++.exe" if executable.endswith(".exe") else "g++"
        ))
        return args
    if executable in ("clang", "clang.exe"):
        args[0] = str(Path(args[0]).with_name(
            "clang++.exe" if executable.endswith(".exe") else "clang++"
        ))
        return args
    return None


def main() -> int:
    attempts = []
    for candidate in test_core_c.compiler_candidates():
        cxx = cpp_args(candidate)
        if cxx is None:
            continue
        resolved, error = test_core_c._resolve_executable(cxx)
        if error:
            attempts.append({
                "compiler": compiler_label(candidate),
                "status": "UNAVAILABLE",
                "error": error,
            })
            continue
        with tempfile.TemporaryDirectory(prefix="transvoxel_m25_") as tmp:
            executable = Path(tmp) / (
                "m25_original_contract.exe"
                if sys.platform == "win32"
                else "m25_original_contract"
            )
            command = [
                *cxx,
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-pedantic",
                f"-I{GENERATED}",
                str(SOURCE),
                "-o",
                str(executable),
            ]
            compiled = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            attempt = {
                "compiler": compiler_label(candidate),
                "compile_returncode": compiled.returncode,
                "compile_stdout": compiled.stdout,
                "compile_stderr": compiled.stderr,
            }
            if compiled.returncode != 0:
                attempt["status"] = "COMPILE_FAIL"
                attempts.append(attempt)
                continue
            ran = subprocess.run(
                [str(executable)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            attempt.update({
                "run_returncode": ran.returncode,
                "stdout": ran.stdout,
                "stderr": ran.stderr,
                "status": "PASS" if ran.returncode == 0 else "RUN_FAIL",
            })
            attempts.append(attempt)
            if ran.returncode == 0:
                report = {
                    "schema": "boqsc.transvoxel.m25.consumer_validation.v1",
                    "status": "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER",
                    "compiler": compiler_label(candidate),
                    "stdout": ran.stdout,
                    "attempts": attempts,
                }
                REPORT.write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                print("M25 original-contract consumer:", report["status"])
                print(ran.stdout, end="")
                return 0
    report = {
        "schema": "boqsc.transvoxel.m25.consumer_validation.v1",
        "status": "FAIL_M25_UNCHANGED_STYLE_CPP_CONSUMER",
        "attempts": attempts,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("M25 original-contract consumer:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
