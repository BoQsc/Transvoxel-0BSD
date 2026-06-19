#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M8: package validation for the selectable M4 backend."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M8_DIR = ROOT / "research" / "official_topology" / "m8"
M7_REPORT = ROOT / "research" / "official_topology" / "m7" / "m7_report.json"
PACKAGE_REPORT = ROOT / "validation" / "m4_backend_c_report.json"
M8_REPORT = M8_DIR / "m8_report.json"
RESULTS = M8_DIR / "results.md"

REQUIRED_PACKAGE_FILES = [
    "include/transvoxel.h",
    "include/transvoxel_m4_candidate.h",
    "include/transvoxel_m4_backend.h",
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "src/transvoxel_m4_backend.c",
    "generated/transvoxel_tables.h",
    "generated/official_topology_candidate_tables.h",
    "examples/c_m4_backend_switch/main.c",
    "examples/c_m4_backend_switch/BUILD_WITH_ZIG.cmd",
    "examples/c_m4_backend_switch/BUILD_WITH_CC.sh",
]


def run_step(command: List[str]) -> Dict[str, object]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="")
    return {
        "command": stable_command(command),
        "returncode": proc.returncode,
        "output": sanitize_output(proc.stdout),
    }


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_command(command: List[str]) -> List[str]:
    out: List[str] = []
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            out.append("python")
        else:
            out.append(item.replace(str(ROOT), "<repo>"))
    return out


def sanitize_output(output: str) -> str:
    out = output.replace(str(ROOT), "<repo>")
    out = out.replace(str(Path(sys.executable)), "python")
    return out


def package_manifest_report() -> Dict[str, Any]:
    sys.path.insert(0, str(ROOT / "tools"))
    import build_dist  # noqa: WPS433

    manifest = set(build_dist.CORE_FILES)
    missing_on_disk = [
        rel for rel in REQUIRED_PACKAGE_FILES
        if not (ROOT / rel).exists()
    ]
    missing_from_manifest = [
        rel for rel in REQUIRED_PACKAGE_FILES
        if rel not in manifest
    ]
    return {
        "status": "PASS" if not missing_on_disk and not missing_from_manifest else "FAIL",
        "manifest_source": "tools/build_dist.py:CORE_FILES",
        "zip_rebuilt": False,
        "zip_path": "dist/transvoxel_0bsd_core.zip",
        "required_files": REQUIRED_PACKAGE_FILES,
        "missing_on_disk": missing_on_disk,
        "missing_from_manifest": missing_from_manifest,
    }


def write_results(
    report: Dict[str, Any],
    package_report: Dict[str, Any],
    manifest_report: Dict[str, Any]) -> None:
    parsed = package_report.get("parsed", {})
    lines = [
        "# M8 M4 Backend Package Proof",
        "",
        "M8 validates the selectable M4 backend as an optional package source path.",
        "It does not rebuild the release zip.",
        "",
        f"- Status: `{report['status']}`",
        f"- M7 status: `{report.get('m7_status')}`",
        f"- Package C validation: `{package_report.get('status')}`",
        f"- Compiler: `{package_report.get('compiler', 'NOT_AVAILABLE')}`",
        f"- Package manifest: `{manifest_report.get('status')}`",
        f"- Zip rebuilt in M8: `{manifest_report.get('zip_rebuilt')}`",
        "",
        "## Package C smoke",
        "",
        f"- Case: `{parsed.get('case')}`",
        f"- Default vertices: `{parsed.get('default_vertices')}`",
        f"- Default triangles: `{parsed.get('default_triangles')}`",
        f"- M4 vertices: `{parsed.get('m4_vertices')}`",
        f"- M4 triangles: `{parsed.get('m4_triangles')}`",
        f"- Default restored: `{parsed.get('restored_default')}`",
        f"- Custom backend after uninstall: `{parsed.get('custom_after')}`",
        "",
        "## Package manifest files checked",
        "",
    ]
    for rel in manifest_report.get("required_files", []):
        lines.append(f"- `{rel}`")
    lines.extend([
        "",
        "## What remains unproven",
        "",
        "- official Transvoxel.cpp byte/table identity;",
        "- official class ID mapping;",
        "- official triangle topology equivalence;",
        "- decision to make M4 the default backend.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m7/run_m7.py"]),
        run_step([sys.executable, "tools/test_m4_backend_c.py"]),
    ]
    m7_report = read_json(M7_REPORT)
    package_report = read_json(PACKAGE_REPORT)
    manifest_report = package_manifest_report()
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m7_report.get("status") == "PASS_M7_NORMAL_API_M4_BACKEND_SWITCH_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and package_report.get("status") == "PASS_M4_BACKEND_PACKAGE_C_EXAMPLE"
        and manifest_report.get("status") == "PASS"
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m8.report.v1",
        "status": (
            "PASS_M8_M4_BACKEND_PACKAGE_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M8_M4_BACKEND_PACKAGE_PROOF"
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "zip_rebuilt": False,
        "steps": steps,
        "outputs": {
            "package_c_validation": str(PACKAGE_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m7_status": m7_report.get("status"),
        "package_c_validation": package_report,
        "package_manifest": manifest_report,
    }
    M8_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, package_report, manifest_report)
    print()
    print("M8:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
