#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build a temporary Godot Voxel GDExtension with the M26 table replacement."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
M26_DIR = ROOT / "research" / "official_topology" / "m26"
CANDIDATE = M26_DIR / "generated" / "transvoxel_tables.cpp"
REPORT = M26_DIR / "m26_full_godot_voxel_build.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def discover_godot_voxel() -> Path:
    configured = os.environ.get("GODOT_VOXEL_REPO")
    candidates = [
        Path(configured) if configured else None,
        Path.home() / "Documents" / "godot_voxel",
    ]
    for candidate in candidates:
        if candidate is not None and (candidate / "SConstruct").is_file():
            return candidate.resolve()
    raise FileNotFoundError("Godot Voxel checkout not found")


def discover_godot_cpp() -> Path:
    configured = os.environ.get("GODOT_CPP_PATH")
    candidates = [
        Path(configured) if configured else None,
        (
            Path.home()
            / "Documents"
            / "gpu-marching-cubes"
            / "addons"
            / "gdextension_setup"
            / "godot-cpp-godot-4.5-stable"
        ),
        (
            Path.home()
            / "Documents"
            / "Playground"
            / "transvoxel_godot"
            / "thirdparty"
            / "godot-cpp"
        ),
        Path.home() / "Documents" / "GDVoxelTerrain" / "godot-cpp",
    ]
    for candidate in candidates:
        if (
            candidate is not None
            and (candidate / "SConstruct").is_file()
            and (
                candidate
                / "bin"
                / "libgodot-cpp.windows.template_debug.x86_64.a"
            ).is_file()
        ):
            return candidate.resolve()
    raise FileNotFoundError(
        "A compatible godot-cpp checkout with a prebuilt debug library was not found"
    )


def discover_zig_support() -> Path:
    candidate = (
        Path.home()
        / "Documents"
        / "Playground"
        / "transvoxel_godot"
        / "thirdparty"
        / "godot-cpp"
    )
    windows_tool = candidate / "tools" / "windows.py"
    if windows_tool.is_file() and "use_zig" in windows_tool.read_text(
        encoding="utf-8", errors="replace"
    ):
        return candidate.resolve()
    raise FileNotFoundError("godot-cpp local use_zig support was not found")


def find_scons() -> str:
    found = shutil.which("scons") or shutil.which("scons.exe")
    if found:
        return found
    candidate = (
        Path(sys.executable).parent / "Scripts" / "scons.exe"
    )
    if candidate.is_file():
        return str(candidate)
    raise FileNotFoundError("scons executable not found")


def find_zig() -> Path:
    configured = os.environ.get("ZIG_EXE")
    if configured and Path(configured).is_file():
        return Path(configured).resolve()
    found = shutil.which("zig") or shutil.which("zig.exe")
    if found:
        return Path(found).resolve()
    candidates = sorted(
        (
            Path.home()
            / "Documents"
            / "gpu-marching-cubes"
            / "addons"
            / "gdextension_setup"
        ).glob("zig-*/zig.exe")
    )
    if candidates:
        return candidates[-1].resolve()
    raise FileNotFoundError("Zig was not found; set ZIG_EXE")


def clone(source: Path, destination: Path) -> None:
    proc = subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-hardlinks",
            str(source),
            str(destination),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git clone failed")


def patch_temp_godot_cpp(
    source: Path,
    zig_support: Path,
    destination: Path,
) -> None:
    for relative in (
        Path("tools/godotcpp.py"),
        Path("tools/my_spawn.py"),
        Path("tools/windows.py"),
    ):
        shutil.copy2(zig_support / relative, destination / relative)
    for directory in ("include", "gdextension"):
        shutil.copytree(
            source / directory,
            destination / directory,
            dirs_exist_ok=True,
        )
    shutil.copytree(
        source / "gen",
        destination / "gen",
        dirs_exist_ok=True,
    )
    (destination / "bin").mkdir(exist_ok=True)
    shutil.copy2(
        (
            source
            / "bin"
            / "libgodot-cpp.windows.template_debug.x86_64.a"
        ),
        destination / "bin",
    )
    sconstruct = destination / "SConstruct"
    text = sconstruct.read_text(encoding="utf-8")
    marker = 'env.PrependENVPath("PATH", os.getenv("PATH"))'
    replacement = "\n".join([
        marker,
        'env["ENV"]["ZIG_GLOBAL_CACHE_DIR"] = os.environ.get(',
        '    "ZIG_GLOBAL_CACHE_DIR", ""',
        ")",
        'env["ENV"]["ZIG_LOCAL_CACHE_DIR"] = os.environ.get(',
        '    "ZIG_LOCAL_CACHE_DIR", ""',
        ")",
        'env["ENV"]["HOME"] = os.environ.get("HOME", "")',
        'env["ENV"]["LOCALAPPDATA"] = os.environ.get("LOCALAPPDATA", "")',
    ])
    if marker not in text:
        raise RuntimeError("godot-cpp SConstruct environment marker missing")
    sconstruct.write_text(
        text.replace(marker, replacement, 1),
        encoding="utf-8",
    )


def stable_tail(output: str, sandbox: Path) -> List[str]:
    sanitized = (
        output.replace(str(sandbox), "<temp>")
        .replace(str(ROOT), "<repo>")
        .replace(str(Path.home()), "<home>")
    )
    lines = sanitized.splitlines()[-160:]
    return [
        line if len(line) <= 800 else line[:800] + "...<truncated>"
        for line in lines
    ]


def main() -> int:
    godot_voxel = discover_godot_voxel()
    godot_cpp = discover_godot_cpp()
    zig_support = discover_zig_support()
    zig_exe = find_zig()
    scons = find_scons()
    with tempfile.TemporaryDirectory(
        prefix="transvoxel_m26_full_",
        ignore_cleanup_errors=True,
    ) as tmp:
        sandbox = Path(tmp)
        voxel_clone = sandbox / "godot_voxel"
        cpp_clone = sandbox / "godot-cpp"
        clone(godot_voxel, voxel_clone)
        clone(zig_support, cpp_clone)
        patch_temp_godot_cpp(godot_cpp, zig_support, cpp_clone)
        shutil.copy2(
            CANDIDATE,
            (
                voxel_clone
                / "meshers"
                / "transvoxel"
                / "transvoxel_tables.cpp"
            ),
        )
        env = dict(os.environ)
        env["GODOT_CPP_PATH"] = str(cpp_clone)
        env["SCONS_CACHE"] = str(ROOT / "build" / "m26_scons_cache")
        env["ZIG_GLOBAL_CACHE_DIR"] = str(sandbox / "zig-global-cache")
        env["ZIG_LOCAL_CACHE_DIR"] = str(sandbox / "zig-local-cache")
        env.setdefault("HOME", str(Path.home()))
        (sandbox / "zig-global-cache").mkdir()
        (sandbox / "zig-local-cache").mkdir()
        (ROOT / "build" / "m26_scons_cache").mkdir(
            parents=True,
            exist_ok=True,
        )
        command = [
            scons,
            "-C",
            str(voxel_clone),
            "target=template_debug",
            "platform=windows",
            "arch=x86_64",
            "precision=single",
            "dev_build=no",
            "use_mingw=yes",
            "use_zig=yes",
            "build_library=no",
            f"zig_root={zig_exe.parent}",
            "-j4",
        ]
        proc = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32"
                else 0
            ),
        )
        timed_out = False
        try:
            output, _ = proc.communicate(timeout=1200)
        except subprocess.TimeoutExpired:
            timed_out = True
            if sys.platform == "win32":
                subprocess.run(
                    [
                        "taskkill",
                        "/PID",
                        str(proc.pid),
                        "/T",
                        "/F",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                proc.kill()
            output, _ = proc.communicate()
        bin_dir = (
            voxel_clone
            / "project"
            / "addons"
            / "zylann.voxel"
            / "bin"
        )
        artifacts: List[Dict[str, object]] = []
        if bin_dir.is_dir():
            for path in sorted(bin_dir.iterdir()):
                if path.is_file():
                    artifacts.append({
                        "name": path.name,
                        "bytes": path.stat().st_size,
                        "sha256": sha256(path),
                    })
        dlls = [
            item for item in artifacts
            if str(item["name"]).lower().endswith(".dll")
        ]
        passed = not timed_out and proc.returncode == 0 and bool(dlls)
        report = {
            "schema": "boqsc.transvoxel.m26.full_godot_voxel_build.v1",
            "status": (
                "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
                if passed
                else "FAIL_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
            ),
            "meaning": (
                "A temporary clone of the pinned Godot Voxel checkout built "
                "as a Windows GDExtension with the M26 table replacement."
            ),
            "returncode": proc.returncode,
            "timed_out": timed_out,
            "compiler": "zig c++ via godot-cpp use_zig SCons integration",
            "command": [
                "scons",
                "-C",
                "<temp>/godot_voxel",
                *[
                    "zig_root=<zig-root>"
                    if value.startswith("zig_root=")
                    else value
                    for value in command[3:-1]
                ],
                "-j4",
            ],
            "output_tail": stable_tail(output, sandbox),
            "artifacts": artifacts,
            "godot_voxel": {
                "origin": git_value(
                    godot_voxel, "remote", "get-url", "origin"
                ),
                "commit": git_value(godot_voxel, "rev-parse", "HEAD"),
            },
            "godot_cpp": {
                "origin": git_value(
                    zig_support, "remote", "get-url", "origin"
                ),
                "commit": git_value(
                    zig_support, "rev-parse", "HEAD"
                ),
                "branch": git_value(
                    zig_support, "branch", "--show-current"
                ),
                "prebuilt_asset_source": (
                    "local godot-cpp-godot-4.5-stable dependency"
                ),
                "local_zig_support_files_copied": [
                    "tools/godotcpp.py",
                    "tools/my_spawn.py",
                    "tools/windows.py",
                ],
                "prebuilt_library_sha256": sha256(
                    (
                        godot_cpp
                        / "bin"
                        / (
                            "libgodot-cpp.windows.template_debug."
                            "x86_64.a"
                        )
                    )
                ),
            },
            "candidate_sha256": sha256(CANDIDATE),
            "temporary_clones_only": True,
        }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("M26 full Godot Voxel build:", report["status"])
    print("artifacts:", len(report["artifacts"]))
    if report["returncode"] != 0:
        for line in report["output_tail"][-20:]:
            print(line)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
