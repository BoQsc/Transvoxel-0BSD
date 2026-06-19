#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run the M4 callback-adapter package example."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "validation" / "m4_backend_c_report.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

VALIDATED_FILES = [
    "include/transvoxel.h",
    "include/transvoxel_m4_candidate.h",
    "include/transvoxel_m4_backend.h",
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "src/transvoxel_m4_backend.c",
    "generated/official_topology_candidate_tables.h",
    "examples/c_m4_backend_switch/main.c",
]

COMPILE_SOURCES = [
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "src/transvoxel_m4_backend.c",
    "examples/c_m4_backend_switch/main.c",
]


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_compiler_label(candidate: Dict[str, Any]) -> str:
    args = list(candidate.get("args", []))
    if candidate.get("kind") == "zig" and len(args) >= 2:
        return "zig cc"
    if args:
        return Path(str(args[0])).name
    return "<empty>"


def stable_source(candidate: Dict[str, Any]) -> Any:
    source = candidate.get("source")
    if source == "cache":
        return "configured-c-compiler"
    if isinstance(source, str) and source.startswith("auto-search:"):
        return "configured-c-compiler"
    if source == "path file":
        return "configured-c-compiler"
    return source


def sanitize_text(text: str, temp_dir: Optional[Path] = None) -> str:
    out = text.replace(str(ROOT), "<repo>")
    if temp_dir is not None:
        out = out.replace(str(temp_dir), "<temp>")
    return out[-4000:]


def build_command(candidate: Dict[str, Any], exe: Path) -> List[str]:
    args = list(candidate["args"])
    if candidate.get("kind") == "msvc":
        return args + [
            "/nologo",
            "/TC",
            "/Iinclude",
            "/Igenerated",
            *[source.replace("/", "\\") for source in COMPILE_SOURCES],
            "/Fe:" + str(exe),
        ]
    return args + [
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-Iinclude",
        "-Igenerated",
        *COMPILE_SOURCES,
        "-o",
        str(exe),
    ]


def stable_command(command: List[str], exe: Path, candidate: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    exe_text = str(exe)
    for index, item in enumerate(command):
        if index == 0:
            if candidate.get("kind") == "zig":
                out.append("zig")
            else:
                out.append(Path(str(item)).name)
        elif item == exe_text:
            out.append("<temp>/c_m4_backend_switch.exe")
        elif item == "/Fe:" + exe_text:
            out.append("/Fe:<temp>/c_m4_backend_switch.exe")
        else:
            out.append(item)
    return out


def parse_key_values(line: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for key, value in re.findall(r"([a-zA-Z0-9_]+)=(-?\d+)", line):
        result[key] = int(value)
    return result


def parse_stdout(stdout: str) -> Tuple[str, Dict[str, int]]:
    for line in stdout.splitlines():
        if line.startswith("m4 package backend "):
            return line, parse_key_values(line)
    return "", {}


def parsed_output_errors(parsed: Dict[str, int]) -> List[str]:
    errors: List[str] = []
    required_exact = {
        "case": 341,
        "default_vertices": 12,
        "default_triangles": 12,
        "m4_vertices": 12,
        "m4_triangles": 12,
        "same_as_default": 1,
        "restored_default": 1,
        "custom_after": 0,
    }
    for key, expected in required_exact.items():
        if parsed.get(key) != expected:
            errors.append(f"{key} expected {expected}, got {parsed.get(key)}")
    return errors


def try_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    label = stable_compiler_label(candidate)
    source = stable_source(candidate)
    _exe_path, resolve_error = test_core_c._resolve_executable(list(candidate.get("args", [])))
    if resolve_error:
        return {
            "candidate": label,
            "source": source,
            "status": "SKIP_UNRESOLVED_COMPILER",
            "error": resolve_error,
        }

    with tempfile.TemporaryDirectory(prefix="transvoxel_m4_package_") as tmp_raw:
        tmp = Path(tmp_raw)
        exe = tmp / ("c_m4_backend_switch.exe" if sys.platform.startswith("win") else "c_m4_backend_switch")
        command = build_command(candidate, exe)
        compile_proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stable = stable_command(command, exe, candidate)
        if compile_proc.returncode != 0:
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_COMPILE",
                "command": stable,
                "returncode": compile_proc.returncode,
                "stdout": sanitize_text(compile_proc.stdout, tmp),
                "stderr": sanitize_text(compile_proc.stderr, tmp),
            }

        run_proc = subprocess.run(
            [str(exe)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        line, parsed = parse_stdout(run_proc.stdout)
        output_errors = parsed_output_errors(parsed)
        if run_proc.returncode != 0 or output_errors:
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_RUN",
                "command": stable,
                "returncode": run_proc.returncode,
                "stdout": sanitize_text(run_proc.stdout, tmp),
                "stderr": sanitize_text(run_proc.stderr, tmp),
                "output_errors": output_errors,
                "parsed": parsed,
            }

        return {
            "candidate": label,
            "source": source,
            "status": "PASS",
            "command": stable,
            "returncode": run_proc.returncode,
            "stdout": line,
            "stderr": sanitize_text(run_proc.stderr, tmp),
            "parsed": parsed,
        }


def main() -> int:
    attempts: List[Dict[str, Any]] = []
    candidates = test_core_c.compiler_candidates()
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_backend_c_report.v1",
        "status": "SKIPPED_NO_C_COMPILER",
        "meaning": (
            "Compiles and runs the M4 backend callback adapter package example "
            "through the normal transvoxel.h API. Since M21 makes clean-room "
            "M4 the default transition path, this proves callback install/"
            "uninstall compatibility rather than a distinct optional topology."
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": True,
        "validated_files": VALIDATED_FILES,
        "attempts": attempts,
    }
    if not candidates:
        report["reason"] = "no C compiler found; add Zig path to c_compiler_path.txt or set ZIG_EXE/CC"
        write_json(REPORT_PATH, report)
        print("M4 backend package C test:", report["status"])
        return 0

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            report.update({
                "status": "PASS_M4_BACKEND_PACKAGE_C_EXAMPLE",
                "compiler": result["candidate"],
                "source": result["source"],
                "checks": [
                    "compiled default clean-room M4 backend and explicit M4 adapter sources together",
                    "public transvoxel.h transition API starts on the default clean-room M4 backend",
                    "default backend builds the max-triangle M4 package smoke case",
                    "M4 callback adapter installs through transvoxel_m4_backend.h",
                    "tv_build_transition_cell preserves M4 behavior after explicit adapter install",
                    "M4 callback adapter uninstalls and restores the default clean-room M4 backend",
                ],
                "stdout": result["stdout"],
                "parsed": result["parsed"],
            })
            write_json(REPORT_PATH, report)
            print("M4 backend package C test:", report["status"])
            print(result["stdout"])
            return 0

    report["status"] = "FAIL_M4_BACKEND_PACKAGE_C_EXAMPLE"
    report["reason"] = "all detected C compiler candidates failed the M4 callback-adapter package example"
    write_json(REPORT_PATH, report)
    print("M4 backend package C test:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
