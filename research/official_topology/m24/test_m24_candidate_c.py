#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and exhaustively run the isolated M24 topology candidate."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M24_DIR = ROOT / "research" / "official_topology" / "m24"
HEADER = M24_DIR / "generated" / "m24_exact_topology_tables.h"
REPORT = M24_DIR / "m24_c_validation.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

C_SOURCE = r'''
#include <stdio.h>
#include "transvoxel.h"

int main(void) {
    int failures = 0;
    int regular_vertices = 0;
    int regular_triangles = 0;
    int transition_vertices = 0;
    int transition_triangles = 0;
    int case_index;

    for (case_index = 0; case_index < 256; ++case_index) {
        float samples[TV_REGULAR_SAMPLE_COUNT];
        TvVec3 vertices[TV_REGULAR_MAX_VERTICES];
        TvTriangle triangles[TV_REGULAR_MAX_TRIANGLES];
        TvBuildInfo info;
        int i;
        for (i = 0; i < TV_REGULAR_SAMPLE_COUNT; ++i) {
            samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
        }
        info = tv_build_regular_cell(
            samples, 0.0f, tv_vec3(0, 0, 0), tv_vec3(1, 1, 1),
            vertices, TV_REGULAR_MAX_VERTICES,
            triangles, TV_REGULAR_MAX_TRIANGLES);
        if (info.result != TV_OK || info.case_index != case_index) {
            ++failures;
        }
        regular_vertices += info.vertex_count;
        regular_triangles += info.triangle_count;
    }

    for (case_index = 0; case_index < 512; ++case_index) {
        float samples[TV_TRANSITION_SAMPLE_COUNT];
        TvVec3 vertices[TV_TRANSITION_MAX_VERTICES];
        TvTriangle triangles[TV_TRANSITION_MAX_TRIANGLES];
        TvBuildInfo info;
        int i;
        for (i = 0; i < TV_TRANSITION_HIGH_SAMPLE_COUNT; ++i) {
            samples[i] = (case_index & (1 << i)) ? -1.0f : 1.0f;
        }
        tv_transition_fill_derived_samples(samples);
        info = tv_build_transition_cell(
            samples, 0.0f, tv_vec3(0, 0, 0), tv_vec3(1, 1, 1),
            vertices, TV_TRANSITION_MAX_VERTICES,
            triangles, TV_TRANSITION_MAX_TRIANGLES);
        if (info.result != TV_OK || info.case_index != case_index) {
            ++failures;
        }
        transition_vertices += info.vertex_count;
        transition_triangles += info.triangle_count;
    }

    printf(
        "m24 candidate regular_vertices=%d regular_triangles=%d "
        "transition_vertices=%d transition_triangles=%d failures=%d\n",
        regular_vertices, regular_triangles,
        transition_vertices, transition_triangles, failures);
    return failures == 0
        && regular_vertices == 1536
        && regular_triangles == 820
        && transition_vertices == 4096
        && transition_triangles == 2640 ? 0 : 1;
}
'''


def stable_compiler(candidate: Dict[str, Any]) -> str:
    args = list(candidate.get("args", []))
    if candidate.get("kind") == "zig" and len(args) >= 2:
        return "zig cc"
    return " ".join(args)


def main() -> int:
    attempts: List[Dict[str, Any]] = []
    if not HEADER.exists():
        raise FileNotFoundError(HEADER)
    for candidate in test_core_c.compiler_candidates():
        resolved, error = test_core_c._resolve_executable(
            list(candidate.get("args", []))
        )
        if error:
            attempts.append({
                "compiler": stable_compiler(candidate),
                "status": "UNAVAILABLE",
                "error": error,
            })
            continue
        with tempfile.TemporaryDirectory(prefix="transvoxel_m24_") as tmp:
            temp = Path(tmp)
            shutil.copy2(HEADER, temp / "transvoxel_tables.h")
            source = temp / "main.c"
            source.write_text(C_SOURCE, encoding="utf-8")
            executable = temp / (
                "m24_candidate.exe" if sys.platform == "win32"
                else "m24_candidate"
            )
            args = list(candidate["args"])
            if candidate.get("kind") == "zig":
                command = [
                    *args,
                    "-std=c99",
                    "-Wall",
                    "-Wextra",
                    "-pedantic",
                    f"-I{temp}",
                    f"-I{ROOT / 'include'}",
                    str(ROOT / "src" / "transvoxel.c"),
                    str(source),
                    "-o",
                    str(executable),
                ]
            else:
                command = [
                    *args,
                    "-std=c99",
                    f"-I{temp}",
                    f"-I{ROOT / 'include'}",
                    str(ROOT / "src" / "transvoxel.c"),
                    str(source),
                    "-o",
                    str(executable),
                ]
            compile_proc = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            attempt: Dict[str, Any] = {
                "compiler": stable_compiler(candidate),
                "compile_returncode": compile_proc.returncode,
                "compile_stdout": compile_proc.stdout,
                "compile_stderr": compile_proc.stderr,
            }
            if compile_proc.returncode != 0:
                attempt["status"] = "COMPILE_FAIL"
                attempts.append(attempt)
                continue
            run_proc = subprocess.run(
                [str(executable)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            attempt.update({
                "run_returncode": run_proc.returncode,
                "stdout": run_proc.stdout,
                "stderr": run_proc.stderr,
                "status": "PASS" if run_proc.returncode == 0 else "RUN_FAIL",
            })
            attempts.append(attempt)
            if run_proc.returncode == 0:
                report = {
                    "schema": "boqsc.transvoxel.m24.c_validation.v1",
                    "status": "PASS_M24_ZIG_EXACT_TOPOLOGY_CANDIDATE",
                    "compiler": stable_compiler(candidate),
                    "stdout": run_proc.stdout,
                    "attempts": attempts,
                }
                REPORT.write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                print("M24 C candidate:", report["status"])
                print(run_proc.stdout, end="")
                return 0
    report = {
        "schema": "boqsc.transvoxel.m24.c_validation.v1",
        "status": "FAIL_M24_CANDIDATE",
        "attempts": attempts,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("M24 C candidate:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
