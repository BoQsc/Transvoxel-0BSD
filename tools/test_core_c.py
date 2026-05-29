#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "validation" / "core_c_report.json"
CACHE = ROOT / "proof" / "c_compiler_cache.json"

EXAMPLES = [
    {
        "name": "c_minimal",
        "source": "examples/c_minimal/main.c",
        "exe_base": "c_minimal",
        "expected_files": [],
        "stdout_contains": ["regular case=", "transition case="],
    },
    {
        "name": "c_terrain_export",
        "source": "examples/c_terrain_export/main.c",
        "exe_base": "terrain_export",
        "expected_files": [
            "terrain_lod_seam.obj",
            "terrain_lod_seam.mtl",
            "terrain_lod_seam_report.txt",
        ],
        "stdout_contains": [
            "wrote terrain_lod_seam.obj",
            "high_lod0 triangles=",
            "transition triangles=",
            "low_lod1 triangles=",
        ],
        "file_contains": {
            "terrain_lod_seam.obj": [
                "o high_lod0_regular_cells",
                "o transition_strip_between_lod0_and_lod1",
                "o low_lod1_regular_cells_scale_2",
            ],
            "terrain_lod_seam_report.txt": [
                "Triangle counts:",
                "transition:",
            ],
        },
    },
]


def _read_path_file(names: List[str]) -> List[str]:
    out: List[str] = []
    for name in names:
        p = ROOT / name
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8", errors="replace").strip().strip('"')
        if raw:
            out.append(raw)
    return out


def _split_command(raw: str) -> List[str]:
    raw = raw.strip()
    if not raw:
        return []
    unquoted = raw.strip('"')
    # If the user pasted only an executable path, do not treat spaces in folders
    # as separators. This is important for paths like "Program Files".
    if Path(unquoted).exists():
        return [unquoted]
    try:
        return shlex.split(raw, posix=(os.name != "nt"))
    except Exception:
        return [unquoted]


def _add_candidate(candidates: List[Dict[str, Any]], args: List[str], source: str) -> None:
    if not args:
        return
    exe = str(args[0]).strip('"')
    name = Path(exe).name.lower()
    kind = "generic"
    if name in ("zig", "zig.exe"):
        kind = "zig"
        # If the candidate is just zig.exe, use Zig's C compiler driver.
        if len(args) == 1:
            args = [exe, "cc"]
        elif len(args) >= 2 and args[1].lower() != "cc":
            args = [exe, "cc"] + args[1:]
    elif name in ("cl", "cl.exe"):
        kind = "msvc"
    candidates.append({"args": args, "source": source, "kind": kind})


def _is_same_platform(cached: Dict[str, Any]) -> bool:
    cached_platform = cached.get("platform")
    cached_os_name = cached.get("os_name")
    if cached_platform and cached_platform != sys.platform:
        return False
    if cached_os_name and cached_os_name != os.name:
        return False
    # Old cache files did not store platform. They are unsafe because a Linux
    # /usr/bin/cc cache can be copied into a Windows zip and then fail.
    if not cached_platform and not cached_os_name:
        return False
    return True


def compiler_candidates() -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    if CACHE.exists():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
            if _is_same_platform(cached):
                args = cached.get("args")
                if isinstance(args, list):
                    _add_candidate(candidates, [str(x) for x in args], "cache")
        except Exception:
            pass

    for raw in _read_path_file([
        "c_compiler_path.txt",
        "C_COMPILER_PATH.txt",
        "zig_path.txt",
        "ZIG_PATH.txt",
    ]):
        _add_candidate(candidates, _split_command(raw), "path file")

    for env_name in ["CC", "C_COMPILER", "ZIG_EXE", "ZIG"]:
        raw = os.environ.get(env_name, "").strip()
        if raw:
            _add_candidate(candidates, _split_command(raw), "env:" + env_name)

    for name in ["zig", "zig.exe", "cc", "gcc", "clang", "cl"]:
        found = shutil.which(name)
        if found:
            _add_candidate(candidates, [found], "PATH:" + name)

    # Useful for this project setup: Zig is sometimes unpacked next to a Godot
    # GDExtension setup rather than added to PATH. Keep this narrow so the runner
    # does not scan the whole disk.
    if os.name == "nt":
        user = os.environ.get("USERPROFILE", "")
        patterns: List[str] = []
        if user:
            patterns.extend([
                str(Path(user) / "Documents" / "gpu-marching-cubes" / "addons" / "gdextension_setup" / "zig-*" / "zig.exe"),
                str(Path(user) / "Documents" / "*" / "addons" / "gdextension_setup" / "zig-*" / "zig.exe"),
                str(Path(user) / "Downloads" / "zig-*" / "zig.exe"),
            ])
        for pat in patterns:
            for found in glob.glob(pat):
                _add_candidate(candidates, [found], "auto-search:" + pat)

    # Deduplicate exact command lines.
    unique: List[Dict[str, Any]] = []
    seen = set()
    for c in candidates:
        key = tuple(str(x).lower() for x in c["args"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    return unique


def _resolve_executable(args: List[str]) -> Tuple[Optional[str], Optional[str]]:
    if not args:
        return None, "empty compiler command"
    exe = str(args[0]).strip('"')
    # Command contains a path, or is absolute.
    if os.path.isabs(exe) or (os.sep in exe) or (os.altsep and os.altsep in exe):
        p = Path(exe)
        if p.exists() and p.is_file():
            return str(p), None
        return None, "compiler executable not found: " + exe
    found = shutil.which(exe)
    if found:
        return found, None
    return None, "compiler executable not found on PATH: " + exe


def build_command(candidate: Dict[str, Any], source: str, exe: Path) -> List[str]:
    args = list(candidate["args"])
    kind = candidate.get("kind")
    if kind == "msvc":
        return args + [
            "/nologo",
            "/TC",
            "/Iinclude",
            "/Igenerated",
            "src\\transvoxel.c",
            source.replace("/", "\\"),
            "/Fe:" + str(exe),
        ]
    # Generic C compiler and Zig's `zig cc` both accept this form.
    return args + [
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-Iinclude",
        "-Igenerated",
        "src/transvoxel.c",
        source,
        "-o",
        str(exe),
    ]


def write_report(report: Dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _compiler_label(candidate: Dict[str, Any]) -> str:
    args = candidate.get("args", [])
    if candidate.get("kind") == "zig" and len(args) >= 2:
        return str(args[0]) + " " + str(args[1])
    return str(args[0]) if args else "<empty>"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _verify_example_outputs(example: Dict[str, Any], run_dir: Path, stdout: str) -> List[str]:
    errors: List[str] = []
    for needle in example.get("stdout_contains", []):
        if needle not in stdout:
            errors.append("stdout missing: " + needle)
    for rel in example.get("expected_files", []):
        path = run_dir / rel
        if not path.exists():
            errors.append("missing output file: " + rel)
        elif path.stat().st_size <= 0:
            errors.append("empty output file: " + rel)
    file_contains = example.get("file_contains", {})
    if isinstance(file_contains, dict):
        for rel, needles in file_contains.items():
            text = _read_text(run_dir / rel)
            for needle in needles:
                if needle not in text:
                    errors.append(rel + " missing: " + needle)
    return errors


def _run_example(candidate: Dict[str, Any], example: Dict[str, Any]) -> Dict[str, Any]:
    name = str(example["name"])
    build_dir = ROOT / "build" / "core_c" / name
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    exe = build_dir / (str(example["exe_base"]) + (".exe" if os.name == "nt" else ""))
    cmd = build_command(candidate, str(example["source"]), exe)

    result: Dict[str, Any] = {
        "name": name,
        "source": example["source"],
        "build_dir": str(build_dir),
        "exe": str(exe),
        "compile_command": cmd,
        "compile_returncode": None,
        "compile_output": "",
        "run_command": [str(exe)],
        "run_returncode": None,
        "run_output": "",
        "output_errors": [],
        "status": "FAIL",
    }

    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as exc:
        result["compile_error"] = repr(exc)
        return result

    result["compile_returncode"] = proc.returncode
    result["compile_output"] = proc.stdout
    if proc.returncode != 0:
        return result

    try:
        run = subprocess.run([str(exe)], cwd=str(build_dir), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as exc:
        result["run_error"] = repr(exc)
        return result

    result["run_returncode"] = run.returncode
    result["run_output"] = run.stdout
    if run.returncode != 0:
        return result

    errors = _verify_example_outputs(example, build_dir, run.stdout)
    result["output_errors"] = errors
    result["status"] = "PASS" if not errors else "FAIL"
    return result


def _write_compiler_cache(candidate: Dict[str, Any]) -> None:
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({
            "args": candidate.get("args", []),
            "kind": candidate.get("kind"),
            "source": candidate.get("source"),
            "platform": sys.platform,
            "os_name": os.name,
        }, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass


def main() -> int:
    candidates = compiler_candidates()
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.core_c_report.v5",
        "status": "SKIPPED",
        "meaning": "Compiles and runs the public C examples: c_minimal and c_terrain_export.",
        "candidates": candidates,
        "selected": None,
        "attempts": [],
        "examples_required": [example["name"] for example in EXAMPLES],
        "platform": sys.platform,
        "os_name": os.name,
    }
    write_report(report)

    if not candidates:
        report["reason"] = "no C compiler found; add Zig path to c_compiler_path.txt or set ZIG_EXE/CC"
        write_report(report)
        print("core C test: SKIPPED (no C compiler found)")
        print("hint: put your zig.exe path into c_compiler_path.txt, or set ZIG_EXE")
        return 0

    last_output = ""
    for candidate in candidates:
        print("trying C compiler:", _compiler_label(candidate))
        resolved, missing_reason = _resolve_executable(list(candidate.get("args", [])))
        if missing_reason:
            attempt = {
                "candidate": candidate,
                "skipped": True,
                "reason": missing_reason,
            }
            report["attempts"].append(attempt)
            write_report(report)
            print("skip:", missing_reason)
            continue

        attempt = {
            "candidate": candidate,
            "resolved_executable": resolved,
            "examples": [],
            "status": "FAIL",
        }
        all_ok = True
        for example in EXAMPLES:
            example_result = _run_example(candidate, example)
            attempt["examples"].append(example_result)
            if example_result.get("compile_output"):
                last_output = str(example_result.get("compile_output", ""))
            if example_result.get("run_output"):
                print(str(example_result.get("run_output", "")), end="")
            if example_result.get("status") != "PASS":
                all_ok = False
                if example_result.get("compile_output"):
                    print(str(example_result.get("compile_output", "")), end="")
                if example_result.get("run_output"):
                    print(str(example_result.get("run_output", "")), end="")
                if example_result.get("output_errors"):
                    print("output errors:", example_result.get("output_errors"))
                break

        attempt["status"] = "PASS" if all_ok else "FAIL"
        report["attempts"].append(attempt)
        write_report(report)

        if all_ok:
            report["selected"] = candidate
            report["status"] = "PASS"
            _write_compiler_cache(candidate)
            write_report(report)
            print("core C test: PASS")
            return 0

    report["status"] = "FAIL"
    report["reason"] = "all detected C compiler candidates failed to compile/run the required C examples"
    write_report(report)
    if last_output:
        print(last_output)
    print("core C test: FAIL compile/run")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
