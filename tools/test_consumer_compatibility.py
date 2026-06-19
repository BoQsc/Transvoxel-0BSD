#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Prove the M21 public consumer compatibility contract."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "validation" / "consumer_compatibility_report.json"
REPORT_MD = ROOT / "validation" / "consumer_compatibility_report.md"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

C_SOURCES = [
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "examples/c_m21_consumer_contract/main.c",
]

VALIDATED_FILES = [
    "include/transvoxel.h",
    "include/transvoxel_m4_candidate.h",
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "generated/transvoxel_tables.h",
    "generated/official_topology_candidate_tables.h",
    "examples/c_m21_consumer_contract/main.c",
    "examples/cpp_consumer/main.cpp",
]


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sanitize_text(text: str, temp_dir: Optional[Path] = None) -> str:
    out = text.replace(str(ROOT), "<repo>")
    out = out.replace(str(ROOT).replace("\\", "/"), "<repo>")
    if temp_dir is not None:
        out = out.replace(str(temp_dir), "<temp>")
        out = out.replace(str(temp_dir).replace("\\", "/"), "<temp>")
    return out[-6000:]


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
    if source == "path file":
        return "configured-c-compiler"
    if isinstance(source, str) and source.startswith("auto-search:"):
        return "configured-c-compiler"
    return source


def stable_command(command: List[str], temp_dir: Path, candidate: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    temp_native = str(temp_dir)
    temp_forward = temp_native.replace("\\", "/")
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    for index, item in enumerate(command):
        text = str(item)
        if index == 0:
            if candidate.get("kind") == "zig":
                out.append("zig")
            else:
                out.append(Path(text).name)
            continue
        out.append(
            text.replace(temp_native, "<temp>")
            .replace(temp_forward, "<temp>")
            .replace(root_native, "<repo>")
            .replace(root_forward, "<repo>")
        )
    return out


def build_c_command(candidate: Dict[str, Any], exe: Path) -> List[str]:
    args = list(candidate["args"])
    if candidate.get("kind") == "msvc":
        return args + [
            "/nologo",
            "/TC",
            "/Iinclude",
            "/Igenerated",
            *[source.replace("/", "\\") for source in C_SOURCES],
            "/Fe:" + str(exe),
        ]
    return args + [
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-Iinclude",
        "-Igenerated",
        *C_SOURCES,
        "-o",
        str(exe),
    ]


def cxx_args_for(candidate: Dict[str, Any]) -> Optional[List[str]]:
    args = list(candidate.get("args", []))
    if not args:
        return None
    exe = str(args[0])
    name = Path(exe).name.lower()
    if candidate.get("kind") == "zig":
        return [exe, "c++"]
    if name in ("clang", "clang.exe"):
        found = shutil.which("clang++") or shutil.which("clang++.exe")
        return [found] if found else None
    if name in ("gcc", "gcc.exe", "cc", "cc.exe"):
        found = shutil.which("g++") or shutil.which("g++.exe") or shutil.which("c++")
        return [found] if found else None
    if name in ("cl", "cl.exe"):
        return args
    return None


def run_c_contract(candidate: Dict[str, Any], temp_dir: Path) -> Dict[str, Any]:
    exe = temp_dir / ("m21_consumer_contract.exe" if os.name == "nt" else "m21_consumer_contract")
    command = build_c_command(candidate, exe)
    compile_proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result: Dict[str, Any] = {
        "status": "FAIL",
        "command": stable_command(command, temp_dir, candidate),
        "compile_returncode": compile_proc.returncode,
        "compile_stdout": sanitize_text(compile_proc.stdout, temp_dir),
        "compile_stderr": sanitize_text(compile_proc.stderr, temp_dir),
        "run_returncode": None,
        "stdout": "",
        "stderr": "",
        "parsed": {},
    }
    if compile_proc.returncode != 0:
        return result

    run_proc = subprocess.run(
        [str(exe)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    parsed = parse_contract_stdout(run_proc.stdout)
    result.update({
        "run_returncode": run_proc.returncode,
        "stdout": sanitize_text(run_proc.stdout, temp_dir),
        "stderr": sanitize_text(run_proc.stderr, temp_dir),
        "parsed": parsed,
        "status": "PASS" if run_proc.returncode == 0 and parsed.get("failures") == 0 else "FAIL",
    })
    return result


def parse_contract_stdout(stdout: str) -> Dict[str, int]:
    parsed: Dict[str, int] = {}
    for key, value in re.findall(r"([A-Za-z0-9_]+)=(-?\d+)", stdout):
        parsed[key] = int(value)
    return parsed


def build_cpp_commands(candidate: Dict[str, Any], temp_dir: Path) -> Optional[Dict[str, List[str]]]:
    cxx = cxx_args_for(candidate)
    if cxx is None:
        return None
    c_args = list(candidate["args"])
    obj = temp_dir / "transvoxel.o"
    exe = temp_dir / ("cpp_consumer.exe" if os.name == "nt" else "cpp_consumer")
    if candidate.get("kind") == "msvc":
        obj = temp_dir / "transvoxel.obj"
        compile_c = c_args + [
            "/nologo",
            "/TC",
            "/Iinclude",
            "/Igenerated",
            "/c",
            "src\\transvoxel.c",
            "/Fo:" + str(obj),
        ]
        compile_cpp = cxx + [
            "/nologo",
            "/EHsc",
            "/Iinclude",
            "/Igenerated",
            "examples\\cpp_consumer\\main.cpp",
            str(obj),
            "/Fe:" + str(exe),
        ]
    else:
        compile_c = c_args + [
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-Iinclude",
            "-Igenerated",
            "-c",
            "src/transvoxel.c",
            "-o",
            str(obj),
        ]
        compile_cpp = cxx + [
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-Iinclude",
            "-Igenerated",
            "examples/cpp_consumer/main.cpp",
            str(obj),
            "-o",
            str(exe),
        ]
    return {"compile_c": compile_c, "compile_cpp": compile_cpp, "run": [str(exe)]}


def run_cpp_smoke(candidate: Dict[str, Any], temp_dir: Path) -> Dict[str, Any]:
    commands = build_cpp_commands(candidate, temp_dir)
    if commands is None:
        return {
            "status": "SKIP_NO_CXX_COMPILER",
            "reason": "no matching C++ compiler found for selected C compiler",
        }
    compile_c = subprocess.run(
        commands["compile_c"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result: Dict[str, Any] = {
        "status": "FAIL",
        "compile_c_command": stable_command(commands["compile_c"], temp_dir, candidate),
        "compile_cpp_command": stable_command(commands["compile_cpp"], temp_dir, candidate),
        "compile_c_returncode": compile_c.returncode,
        "compile_c_stdout": sanitize_text(compile_c.stdout, temp_dir),
        "compile_c_stderr": sanitize_text(compile_c.stderr, temp_dir),
        "compile_cpp_returncode": None,
        "compile_cpp_stdout": "",
        "compile_cpp_stderr": "",
        "run_returncode": None,
        "stdout": "",
        "stderr": "",
        "parsed": {},
    }
    if compile_c.returncode != 0:
        return result

    compile_cpp = subprocess.run(
        commands["compile_cpp"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result.update({
        "compile_cpp_returncode": compile_cpp.returncode,
        "compile_cpp_stdout": sanitize_text(compile_cpp.stdout, temp_dir),
        "compile_cpp_stderr": sanitize_text(compile_cpp.stderr, temp_dir),
    })
    if compile_cpp.returncode != 0:
        return result

    run_proc = subprocess.run(
        commands["run"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    parsed = parse_contract_stdout(run_proc.stdout)
    result.update({
        "run_returncode": run_proc.returncode,
        "stdout": sanitize_text(run_proc.stdout, temp_dir),
        "stderr": sanitize_text(run_proc.stderr, temp_dir),
        "parsed": parsed,
        "status": "PASS" if run_proc.returncode == 0 and parsed.get("vertices") == 12 and parsed.get("triangles") == 12 else "FAIL",
    })
    return result


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
    with tempfile.TemporaryDirectory(prefix="transvoxel_m21_consumer_") as tmp_raw:
        tmp = Path(tmp_raw)
        c_contract = run_c_contract(candidate, tmp)
        if c_contract["status"] != "PASS":
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_C_CONTRACT",
                "c_contract": c_contract,
            }
        cpp_smoke = run_cpp_smoke(candidate, tmp)
        if cpp_smoke["status"] != "PASS":
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_CPP_CONSUMER",
                "c_contract": c_contract,
                "cpp_smoke": cpp_smoke,
            }
        return {
            "candidate": label,
            "source": source,
            "status": "PASS",
            "c_contract": c_contract,
            "cpp_smoke": cpp_smoke,
        }


def write_markdown(report: Dict[str, Any]) -> None:
    lines = [
        "# M21 Consumer Compatibility Contract",
        "",
        f"Status: `{report['status']}`",
        "",
        f"Functional compatibility: `{report.get('functional_transvoxel_cpp_consumer_compatibility')}`",
        f"Default transition backend: `{report.get('default_transition_backend')}`",
        f"Compiler: `{report.get('compiler', 'n/a')}`",
        "",
        "## Contract",
        "",
        "- Public C API callers use `tv_build_regular_cell()` and `tv_build_transition_cell()`.",
        "- C++ consumers can include `transvoxel.h` and link a C-compiled object through `extern \"C\"`.",
        "- The default transition backend is clean-room M4 published-topology behavior.",
        "- `TV_TRANSITION_SAMPLE_COUNT` remains 14 for ABI compatibility; sample 13 is ignored by the default M4 path.",
        "- Callback customization is retained and reset restores the default M4 backend.",
        "- Exact official table layout, class IDs, vertex encoding, and bytes are not claimed.",
        "",
    ]
    metrics = report.get("metrics", {})
    if metrics:
        lines.extend([
            "## Metrics",
            "",
            f"- Cases: `{metrics.get('cases')}`",
            f"- Default vertices: `{metrics.get('default_vertices')}`",
            f"- Default triangles: `{metrics.get('default_triangles')}`",
            f"- Max vertices/case: `{metrics.get('max_vertices')}`",
            f"- Max triangles/case: `{metrics.get('max_triangles')}`",
            f"- M4 matches: `{metrics.get('m4_matches')}`",
            f"- Sample 13 ignored checks: `{metrics.get('sample13_ignored')}`",
            "",
        ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    attempts: List[Dict[str, Any]] = []
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m21.consumer_compatibility.v1",
        "status": "SKIPPED_NO_C_COMPILER",
        "meaning": (
            "Tests the functional public-consumer contract for the clean-room "
            "Transvoxel.cpp replacement claim. This is not an exact official "
            "table-layout or byte-identity claim."
        ),
        "functional_transvoxel_cpp_consumer_compatibility": "NOT_PROVEN",
        "default_transition_backend": "clean_room_m4_published_topology",
        "default_transition_source": "generated/official_topology_candidate_tables.json via generated/transvoxel_tables.h",
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "exact_table_layout_compatibility": False,
        "validated_files": VALIDATED_FILES,
        "attempts": attempts,
        "contract": {
            "behavioral_replacement_not_byte_identity": True,
            "public_c_api": True,
            "cpp_include_link_smoke": True,
            "callback_customization": True,
            "default_m4_equivalence_all_512": True,
            "sample13_abi_retained_ignored": True,
            "exact_table_layout_compatibility": False,
        },
    }

    candidates = test_core_c.compiler_candidates()
    if not candidates:
        report["reason"] = "no C compiler found; add Zig path to c_compiler_path.txt or set ZIG_EXE/CC"
        write_json(REPORT_JSON, report)
        write_markdown(report)
        print("consumer compatibility test:", report["status"])
        return 0

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            parsed = result["c_contract"]["parsed"]
            report.update({
                "status": "PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY",
                "functional_transvoxel_cpp_consumer_compatibility": "PROVEN",
                "compiler": result["candidate"],
                "source": result["source"],
                "checks": [
                    "compiled and ran exhaustive C consumer contract over all 512 transition cases",
                    "default tv_build_transition_cell output matched direct M4 output for every case",
                    "public transition max constants are 12 vertices and 12 triangles",
                    "public 14-sample ABI retained and sample 13 ignored by default M4 backend",
                    "small-buffer errors are still reported through the public API",
                    "transition callback customization still routes and reset restores default M4",
                    "C++ consumer included transvoxel.h and linked against a C object",
                ],
                "metrics": {
                    "cases": parsed.get("cases"),
                    "default_vertices": parsed.get("default_vertices"),
                    "default_triangles": parsed.get("default_triangles"),
                    "max_vertices": parsed.get("max_vertices"),
                    "max_triangles": parsed.get("max_triangles"),
                    "m4_matches": parsed.get("m4_matches"),
                    "sample13_ignored": parsed.get("sample13_ignored"),
                    "callback_checks": parsed.get("callback_checks"),
                    "failures": parsed.get("failures"),
                },
                "c_stdout": result["c_contract"]["stdout"],
                "cpp_stdout": result["cpp_smoke"]["stdout"],
            })
            write_json(REPORT_JSON, report)
            write_markdown(report)
            print("consumer compatibility test:", report["status"])
            print(result["c_contract"]["stdout"])
            print(result["cpp_smoke"]["stdout"])
            return 0

    report["status"] = "FAIL_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY"
    report["reason"] = "all detected compiler candidates failed the M21 consumer compatibility contract"
    write_json(REPORT_JSON, report)
    write_markdown(report)
    print("consumer compatibility test:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
