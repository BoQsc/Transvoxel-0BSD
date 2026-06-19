#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and run M15 six-face M4 orientation validation with Zig."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M15_DIR = ROOT / "research" / "official_topology" / "m15"
REPORT_PATH = M15_DIR / "m15_c_validation.json"

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
        "examples/c_m15_m4_six_faces/main.c",
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
            out.append("<temp>/m15_m4_six_faces.exe")
        else:
            out.append(item)
    return out


def parse_key_values(line: str) -> Dict[str, int]:
    return {
        key: int(value)
        for key, value in re.findall(r"([a-zA-Z0-9_]+)=(-?\d+)", line)
    }


def parse_stdout(stdout: str) -> Dict[str, Any]:
    faces: List[Dict[str, int]] = []
    totals: Dict[str, int] = {}
    for line in stdout.splitlines():
        if line.startswith("m15 face "):
            faces.append(parse_key_values(line))
        elif line.startswith("m15 totals "):
            totals = parse_key_values(line)
    return {"faces": faces, "totals": totals}


def parsed_output_errors(parsed: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    faces = parsed["faces"]
    totals = parsed["totals"]
    if len(faces) != 6:
        errors.append(f"expected 6 face records, got {len(faces)}")
    expected_face = {
        "cases": 512,
        "vertices": 4096,
        "triangles": 2640,
        "invalid_triangles": 0,
        "degenerate_triangles": 0,
        "transform_failures": 0,
        "orientation_failures": 0,
        "frame_failures": 0,
        "seam_builds": 448,
        "shared_faces": 672,
        "seam_failures": 0,
        "seam_vertices": 1616,
        "seam_triangles": 1020,
    }
    for face_id, face in enumerate(faces):
        if face.get("id") != face_id:
            errors.append(
                f"face record {face_id} has id {face.get('id')}"
            )
        for key, expected in expected_face.items():
            if face.get(key) != expected:
                errors.append(
                    f"face {face_id} {key} expected {expected}, got {face.get(key)}"
                )
    expected_totals = {
        "faces": 6,
        "failed_faces": 0,
        "cases": 3072,
        "vertices": 24576,
        "triangles": 15840,
        "invalid_triangles": 0,
        "degenerate_triangles": 0,
        "transform_failures": 0,
        "orientation_failures": 0,
        "frame_failures": 0,
        "seam_builds": 2688,
        "shared_faces": 4032,
        "seam_failures": 0,
        "seam_vertices": 9696,
        "seam_triangles": 6120,
    }
    for key, expected in expected_totals.items():
        if totals.get(key) != expected:
            errors.append(
                f"totals {key} expected {expected}, got {totals.get(key)}"
            )
    return errors


def try_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    _, resolve_error = test_core_c._resolve_executable(candidate["args"])
    if resolve_error:
        return {
            "candidate": "zig cc",
            "source": stable_source(candidate),
            "status": "SKIP_UNRESOLVED_COMPILER",
            "error": resolve_error,
        }

    with tempfile.TemporaryDirectory(prefix="transvoxel_m15_zig_") as tmp:
        exe = Path(tmp) / (
            "m15_m4_six_faces.exe"
            if sys.platform.startswith("win")
            else "m15_m4_six_faces"
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
        errors = parsed_output_errors(parsed)
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
            "schema": "boqsc.transvoxel.official_topology.m15.c_validation.v1",
            "status": "FAIL_MISSING_ZIG",
            "ok": False,
            "reason": "Zig is required for M15 six-face C validation.",
            "attempts": [],
        }
        write_json(REPORT_PATH, report)
        print("M15 C six-face validation:", report["status"])
        return 1

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            report = {
                "schema": "boqsc.transvoxel.official_topology.m15.c_validation.v1",
                "status": "PASS_M15_ZIG_M4_SIX_FACE_ORIENTATION_VALIDATION",
                "ok": True,
                "compiler": result["candidate"],
                "source": result["source"],
                "validated_files": [
                    "include/transvoxel_m4_candidate.h",
                    "src/transvoxel_m4_candidate.c",
                    "examples/c_m15_m4_six_faces/main.c",
                ],
                "checks": [
                    "compiled the oriented M4 runtime with Zig C99",
                    "validated explicit right-handed frames for +X/-X/+Y/-Y/+Z/-Z",
                    "validated all 512 cases in every face frame",
                    "validated transformed vertex round trips",
                    "validated determinant-aware triangle orientation",
                    "validated nondegenerate triangles in every orientation",
                    "validated deterministic neighbor seams in every orientation",
                ],
                "faces": result["parsed"]["faces"],
                "totals": result["parsed"]["totals"],
                "stdout": result["stdout"],
                "attempts": attempts,
            }
            write_json(REPORT_PATH, report)
            print("M15 C six-face validation:", report["status"])
            print(result["stdout"])
            return 0

    report = {
        "schema": "boqsc.transvoxel.official_topology.m15.c_validation.v1",
        "status": "FAIL_M15_ZIG_M4_SIX_FACE_ORIENTATION_VALIDATION",
        "ok": False,
        "attempts": attempts,
    }
    write_json(REPORT_PATH, report)
    print("M15 C six-face validation:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
