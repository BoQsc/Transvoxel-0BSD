#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Compile and compare the pinned Godot Voxel table API with the M26 replacement."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
M26_DIR = ROOT / "research" / "official_topology" / "m26"
CONSUMER = M26_DIR / "godot_style_table_consumer.cpp"
CANDIDATE = M26_DIR / "generated" / "transvoxel_tables.cpp"
REPORT = M26_DIR / "m26_godot_voxel_integration.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_godot_voxel() -> Path:
    candidates = []
    configured = os.environ.get("GODOT_VOXEL_REPO")
    if configured:
        candidates.append(Path(configured))
    candidates.append(Path.home() / "Documents" / "godot_voxel")
    for candidate in candidates:
        table = candidate / "meshers" / "transvoxel" / "transvoxel_tables.cpp"
        if table.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Godot Voxel checkout not found; set GODOT_VOXEL_REPO"
    )


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


def git_value(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def prepare_tree(root: Path, source: Path) -> None:
    table_dir = root / "meshers" / "transvoxel"
    util_dir = root / "util"
    table_dir.mkdir(parents=True)
    util_dir.mkdir(parents=True)
    shutil.copy2(source, table_dir / "transvoxel_tables.cpp")
    (util_dir / "errors.h").write_text(
        "#pragma once\n"
        "#include <cassert>\n"
        "#define ZN_ASSERT(condition) assert(condition)\n",
        encoding="utf-8",
    )


def compile_and_run(
    cxx: List[str],
    include_root: Path,
    executable: Path,
) -> Dict[str, Any]:
    command = [
        *cxx,
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-pedantic",
        f"-I{include_root}",
        str(CONSUMER),
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
    result: Dict[str, Any] = {
        "compile_returncode": compiled.returncode,
        "compile_stdout": compiled.stdout,
        "compile_stderr": compiled.stderr,
    }
    if compiled.returncode != 0:
        return result
    ran = subprocess.run(
        [str(executable)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result.update({
        "run_returncode": ran.returncode,
        "stdout": ran.stdout,
        "stderr": ran.stderr,
    })
    return result


def records(output: str) -> Dict[Tuple[str, int], str]:
    result: Dict[Tuple[str, int], str] = {}
    for line in output.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3 or parts[0] not in {"R", "T", "C"}:
            raise ValueError(f"unexpected consumer output: {line!r}")
        result[(parts[0], int(parts[1]))] = parts[2]
    return result


def compare_records(
    original: Dict[Tuple[str, int], str],
    candidate: Dict[Tuple[str, int], str],
) -> Dict[str, Any]:
    expected_keys = {
        *(("R", i) for i in range(256)),
        *(("T", i) for i in range(512)),
        *(("C", i) for i in range(13)),
    }
    mismatches = []
    for key in sorted(expected_keys):
        if original.get(key) != candidate.get(key):
            mismatches.append({
                "kind": key[0],
                "case": key[1],
                "original": original.get(key),
                "candidate": candidate.get(key),
            })
    return {
        "expected_record_count": len(expected_keys),
        "original_record_count": len(original),
        "candidate_record_count": len(candidate),
        "regular_case_matches": sum(
            original.get(("R", i)) == candidate.get(("R", i))
            for i in range(256)
        ),
        "transition_case_matches": sum(
            original.get(("T", i)) == candidate.get(("T", i))
            for i in range(512)
        ),
        "transition_corner_matches": sum(
            original.get(("C", i)) == candidate.get(("C", i))
            for i in range(13)
        ),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:20],
    }


def main() -> int:
    godot_voxel = discover_godot_voxel()
    original_table = (
        godot_voxel
        / "meshers"
        / "transvoxel"
        / "transvoxel_tables.cpp"
    )
    attempts = []
    for compiler in test_core_c.compiler_candidates():
        cxx = cpp_args(compiler)
        if cxx is None:
            continue
        resolved, error = test_core_c._resolve_executable(cxx)
        if error:
            attempts.append({"compiler": cxx, "error": error})
            continue
        with tempfile.TemporaryDirectory(prefix="transvoxel_m26_") as tmp:
            tmp_path = Path(tmp)
            original_root = tmp_path / "original"
            candidate_root = tmp_path / "candidate"
            prepare_tree(original_root, original_table)
            prepare_tree(candidate_root, CANDIDATE)
            original_run = compile_and_run(
                cxx,
                original_root,
                tmp_path / "original_consumer.exe",
            )
            candidate_run = compile_and_run(
                cxx,
                candidate_root,
                tmp_path / "candidate_consumer.exe",
            )
            attempt = {
                "compiler": "zig c++" if compiler.get("kind") == "zig" else cxx,
                "original": {
                    key: value
                    for key, value in original_run.items()
                    if key != "stdout"
                },
                "candidate": {
                    key: value
                    for key, value in candidate_run.items()
                    if key != "stdout"
                },
            }
            if (
                original_run.get("run_returncode") != 0
                or candidate_run.get("run_returncode") != 0
            ):
                attempt["status"] = "COMPILE_OR_RUN_FAIL"
                attempts.append(attempt)
                continue
            comparison = compare_records(
                records(str(original_run["stdout"])),
                records(str(candidate_run["stdout"])),
            )
            attempt["comparison"] = comparison
            attempt["status"] = (
                "PASS" if comparison["mismatch_count"] == 0 else "MISMATCH"
            )
            attempts.append(attempt)
            if attempt["status"] == "PASS":
                repo_status = git_value(godot_voxel, "status", "--porcelain=v1")
                report = {
                    "schema": (
                        "boqsc.transvoxel.m26."
                        "godot_voxel_integration.v1"
                    ),
                    "status": (
                        "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION"
                    ),
                    "meaning": (
                        "The M26 replacement compiles against the actual "
                        "Godot Voxel table API and matches every exhaustive "
                        "Godot-style regular/transition output record."
                    ),
                    "compiler": attempt["compiler"],
                    "comparison": comparison,
                    "godot_voxel": {
                        "origin": git_value(
                            godot_voxel, "remote", "get-url", "origin"
                        ),
                        "commit": git_value(
                            godot_voxel, "rev-parse", "HEAD"
                        ),
                        "worktree_clean": repo_status == "",
                        "table_sha256": sha256(original_table),
                        "source_file": (
                            "meshers/transvoxel/transvoxel_tables.cpp"
                        ),
                    },
                    "candidate": {
                        "table_sha256": sha256(CANDIDATE),
                        "source_file": str(
                            CANDIDATE.relative_to(ROOT)
                        ).replace("\\", "/"),
                        "license_status": (
                            "RESEARCH_ONLY_NOT_CLEARED_FOR_0BSD_RELEASE"
                        ),
                    },
                    "full_godot_module_build": {
                        "performed_in_this_step": False,
                        "reason": (
                            "The full temporary GDExtension build is performed "
                            "by test_full_godot_voxel_build.py and recorded in "
                            "m26_full_godot_voxel_build.json."
                        ),
                    },
                    "attempts": attempts,
                }
                REPORT.write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                print("M26 Godot Voxel integration:", report["status"])
                print(
                    "regular={regular_case_matches}/256 "
                    "transition={transition_case_matches}/512 "
                    "corners={transition_corner_matches}/13 "
                    "mismatches={mismatch_count}".format(**comparison)
                )
                return 0
    report = {
        "schema": "boqsc.transvoxel.m26.godot_voxel_integration.v1",
        "status": "FAIL_M26_GODOT_VOXEL_TABLE_INTEGRATION",
        "attempts": attempts,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("M26 Godot Voxel integration:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
