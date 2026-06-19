#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate default clean-room M4 terrain export and the M4 callback adapter."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "validation" / "m4_terrain_c_report.json"

sys.path.insert(0, str(ROOT / "tools"))
import test_core_c  # noqa: E402

OUTPUT_FILES = [
    "terrain_lod_seam.obj",
    "terrain_lod_seam.mtl",
    "terrain_lod_seam_report.txt",
]

COMMON_SOURCES = [
    "src/transvoxel.c",
    "examples/c_terrain_export/main.c",
]

M4_SOURCES = [
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "src/transvoxel_m4_backend.c",
    "examples/c_terrain_export/main.c",
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
    if source == "path file":
        return "configured-c-compiler"
    if isinstance(source, str) and source.startswith("auto-search:"):
        return "configured-c-compiler"
    return source


def sanitize_text(text: str, temp_dir: Optional[Path] = None) -> str:
    out = text.replace(str(ROOT), "<repo>")
    if temp_dir is not None:
        out = out.replace(str(temp_dir), "<temp>")
    return out[-4000:]


def build_command(candidate: Dict[str, Any], mode: str, exe: Path) -> List[str]:
    args = list(candidate["args"])
    sources = M4_SOURCES if mode == "m4" else COMMON_SOURCES
    if candidate.get("kind") == "msvc":
        defines = ["/DTV_EXAMPLE_USE_M4_BACKEND_CANDIDATE"] if mode == "m4" else []
        return args + [
            "/nologo",
            "/TC",
            "/Iinclude",
            "/Igenerated",
            *defines,
            *[source.replace("/", "\\") for source in sources],
            "/Fe:" + str(exe),
        ]
    defines = ["-DTV_EXAMPLE_USE_M4_BACKEND_CANDIDATE"] if mode == "m4" else []
    return args + [
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-Iinclude",
        "-Igenerated",
        *defines,
        *sources,
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
            out.append("<temp>/" + exe.name)
        elif item == "/Fe:" + exe_text:
            out.append("/Fe:<temp>/" + exe.name)
        else:
            out.append(item)
    return out


def parse_stdout(stdout: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "backend": None,
        "high_lod0_triangles": None,
        "transition_triangles": None,
        "low_lod1_triangles": None,
    }
    backend_match = re.search(r"transition backend=([A-Za-z0-9_]+)", stdout)
    if backend_match:
        result["backend"] = backend_match.group(1)
    count_match = re.search(
        r"high_lod0 triangles=(\d+) transition triangles=(\d+) low_lod1 triangles=(\d+)",
        stdout,
    )
    if count_match:
        result["high_lod0_triangles"] = int(count_match.group(1))
        result["transition_triangles"] = int(count_match.group(2))
        result["low_lod1_triangles"] = int(count_match.group(3))
    return result


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def verify_outputs(run_dir: Path, expected_backend: str) -> List[str]:
    errors: List[str] = []
    for rel in OUTPUT_FILES:
        path = run_dir / rel
        if not path.exists():
            errors.append("missing output file: " + rel)
        elif path.stat().st_size <= 0:
            errors.append("empty output file: " + rel)

    obj = read_text(run_dir / "terrain_lod_seam.obj")
    for needle in [
        "o high_lod0_regular_cells",
        "o transition_strip_between_lod0_and_lod1",
        "o low_lod1_regular_cells_scale_2",
        "Transition backend: " + expected_backend,
    ]:
        if needle not in obj:
            errors.append("terrain_lod_seam.obj missing: " + needle)

    report = read_text(run_dir / "terrain_lod_seam_report.txt")
    for needle in [
        "Transition backend: " + expected_backend,
        "Triangle counts:",
        "transition:",
    ]:
        if needle not in report:
            errors.append("terrain_lod_seam_report.txt missing: " + needle)
    return errors


def run_mode(candidate: Dict[str, Any], base_dir: Path, mode: str) -> Dict[str, Any]:
    run_dir = base_dir / mode
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    exe = run_dir / (f"terrain_export_{mode}.exe" if sys.platform.startswith("win") else f"terrain_export_{mode}")
    command = build_command(candidate, mode, exe)
    compile_proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result: Dict[str, Any] = {
        "mode": mode,
        "command": stable_command(command, exe, candidate),
        "compile_returncode": compile_proc.returncode,
        "compile_stdout": sanitize_text(compile_proc.stdout, base_dir),
        "compile_stderr": sanitize_text(compile_proc.stderr, base_dir),
        "run_returncode": None,
        "stdout": "",
        "stderr": "",
        "parsed": {},
        "output_errors": [],
        "status": "FAIL",
    }
    if compile_proc.returncode != 0:
        return result

    run_proc = subprocess.run(
        [str(exe)],
        cwd=run_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    parsed = parse_stdout(run_proc.stdout)
    expected_backend = "m4_callback_adapter" if mode == "m4" else "default_clean_room_m4"
    output_errors = verify_outputs(run_dir, expected_backend)
    if parsed.get("backend") != expected_backend:
        output_errors.append(
            f"stdout backend expected {expected_backend}, got {parsed.get('backend')}"
        )
    for key in ["high_lod0_triangles", "transition_triangles", "low_lod1_triangles"]:
        if not isinstance(parsed.get(key), int) or int(parsed.get(key) or 0) <= 0:
            output_errors.append(f"stdout {key} must be positive, got {parsed.get(key)}")

    result.update({
        "run_returncode": run_proc.returncode,
        "stdout": sanitize_text(run_proc.stdout, base_dir),
        "stderr": sanitize_text(run_proc.stderr, base_dir),
        "parsed": parsed,
        "output_errors": output_errors,
        "status": "PASS" if run_proc.returncode == 0 and not output_errors else "FAIL",
    })
    return result


def compare_modes(default: Dict[str, Any], m4: Dict[str, Any]) -> Dict[str, Any]:
    default_counts = default.get("parsed", {})
    m4_counts = m4.get("parsed", {})
    errors: List[str] = []
    if default_counts.get("high_lod0_triangles") != m4_counts.get("high_lod0_triangles"):
        errors.append("regular high LOD triangle count changed")
    if default_counts.get("low_lod1_triangles") != m4_counts.get("low_lod1_triangles"):
        errors.append("regular low LOD triangle count changed")
    if default_counts.get("transition_triangles") != m4_counts.get("transition_triangles"):
        errors.append("transition strip triangle count changed under M4 callback adapter")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "default": default_counts,
        "m4": m4_counts,
    }


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

    with tempfile.TemporaryDirectory(prefix="transvoxel_m4_terrain_") as tmp_raw:
        tmp = Path(tmp_raw)
        default = run_mode(candidate, tmp, "default")
        if default["status"] != "PASS":
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_DEFAULT_TERRAIN_EXPORT",
                "default": default,
            }
        m4 = run_mode(candidate, tmp, "m4")
        if m4["status"] != "PASS":
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_M4_TERRAIN_EXPORT",
                "default": default,
                "m4": m4,
            }
        comparison = compare_modes(default, m4)
        if comparison["status"] != "PASS":
            return {
                "candidate": label,
                "source": source,
                "status": "FAIL_TERRAIN_COMPARISON",
                "default": default,
                "m4": m4,
                "comparison": comparison,
            }
        return {
            "candidate": label,
            "source": source,
            "status": "PASS",
            "default": default,
            "m4": m4,
            "comparison": comparison,
        }


def main() -> int:
    attempts: List[Dict[str, Any]] = []
    candidates = test_core_c.compiler_candidates()
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.m4_terrain_c_report.v1",
        "status": "SKIPPED_NO_C_COMPILER",
        "meaning": (
            "Compiles and runs the terrain OBJ export path with the default "
            "clean-room M4 transition backend and with the explicit M4 "
            "callback adapter installed through the normal transvoxel.h API."
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": True,
        "validated_files": [
            "include/transvoxel.h",
            "include/transvoxel_m4_candidate.h",
            "include/transvoxel_m4_backend.h",
            "src/transvoxel.c",
            "src/transvoxel_m4_candidate.c",
            "src/transvoxel_m4_backend.c",
            "generated/transvoxel_tables.h",
            "generated/official_topology_candidate_tables.h",
            "examples/c_terrain_export/main.c",
        ],
        "attempts": attempts,
    }
    if not candidates:
        report["reason"] = "no C compiler found; add Zig path to c_compiler_path.txt or set ZIG_EXE/CC"
        write_json(REPORT_PATH, report)
        print("M4 terrain C test:", report["status"])
        return 0

    for candidate in candidates:
        result = try_candidate(candidate)
        attempts.append(result)
        if result["status"] == "PASS":
            comparison = result["comparison"]
            report.update({
                "status": "PASS_M4_TERRAIN_NORMAL_API_EXPORT",
                "compiler": result["candidate"],
                "source": result["source"],
                "checks": [
                    "compiled terrain export with the default clean-room M4 backend",
                    "compiled terrain export with the M4 callback adapter installed",
                    "both modes wrote OBJ, MTL, and terrain reports",
                    "regular high-LOD and low-LOD triangle counts stayed unchanged",
                    "transition-strip triangle count stayed unchanged through the adapter",
                    "default and adapter paths both use the normal tv_build_transition_cell terrain call pattern",
                ],
                "default": comparison["default"],
                "m4": comparison["m4"],
                "comparison": comparison,
            })
            write_json(REPORT_PATH, report)
            print("M4 terrain C test:", report["status"])
            print(
                "default transition triangles={default_t} adapter transition triangles={m4_t}".format(
                    default_t=comparison["default"].get("transition_triangles"),
                    m4_t=comparison["m4"].get("transition_triangles"),
                )
            )
            return 0

    report["status"] = "FAIL_M4_TERRAIN_NORMAL_API_EXPORT"
    report["reason"] = "all detected C compiler candidates failed the M4 terrain export validation"
    write_json(REPORT_PATH, report)
    print("M4 terrain C test:", report["status"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
