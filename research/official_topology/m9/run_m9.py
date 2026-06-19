#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M9: M4 backend through the terrain OBJ export path."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M9_DIR = ROOT / "research" / "official_topology" / "m9"
M8_REPORT = ROOT / "research" / "official_topology" / "m8" / "m8_report.json"
TERRAIN_REPORT = ROOT / "validation" / "m4_terrain_c_report.json"
M9_REPORT = M9_DIR / "m9_report.json"
RESULTS = M9_DIR / "results.md"


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


def write_results(report: Dict[str, Any], terrain_report: Dict[str, Any]) -> None:
    default = terrain_report.get("default", {})
    m4 = terrain_report.get("m4", {})
    comparison = terrain_report.get("comparison", {})
    lines = [
        "# M9 M4 Terrain Export Proof",
        "",
        "M9 validates the selectable M4 backend through the terrain OBJ export path.",
        "",
        f"- Status: `{report['status']}`",
        f"- M8 status: `{report.get('m8_status')}`",
        f"- Terrain C validation: `{terrain_report.get('status')}`",
        f"- Compiler: `{terrain_report.get('compiler', 'NOT_AVAILABLE')}`",
        f"- Default core replaced: `{report.get('default_core_replaced')}`",
        "",
        "## Terrain export comparison",
        "",
        f"- Default backend: `{default.get('backend')}`",
        f"- M4 backend: `{m4.get('backend')}`",
        f"- High LOD triangles default/M4: `{default.get('high_lod0_triangles')}` / `{m4.get('high_lod0_triangles')}`",
        f"- Transition triangles default/M4: `{default.get('transition_triangles')}` / `{m4.get('transition_triangles')}`",
        f"- Low LOD triangles default/M4: `{default.get('low_lod1_triangles')}` / `{m4.get('low_lod1_triangles')}`",
        f"- Comparison status: `{comparison.get('status')}`",
        "",
        "## What passed",
        "",
    ]
    for check in terrain_report.get("checks", []):
        lines.append(f"- {check};")
    lines.extend([
        "",
        "## What remains unproven",
        "",
        "- Godot runtime terrain export through the M4 backend;",
        "- official Transvoxel.cpp byte/table identity;",
        "- official class ID mapping;",
        "- official triangle topology equivalence;",
        "- decision to make M4 the default backend.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m8/run_m8.py"]),
        run_step([sys.executable, "tools/test_m4_terrain_c.py"]),
    ]
    m8_report = read_json(M8_REPORT)
    terrain_report = read_json(TERRAIN_REPORT)
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m8_report.get("status") == "PASS_M8_M4_BACKEND_PACKAGE_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and terrain_report.get("status") == "PASS_M4_TERRAIN_NORMAL_API_EXPORT"
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m9.report.v1",
        "status": (
            "PASS_M9_M4_TERRAIN_EXPORT_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M9_M4_TERRAIN_EXPORT_PROOF"
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "godot_runtime_m4_backend_validated": False,
        "zip_rebuilt": False,
        "steps": steps,
        "outputs": {
            "terrain_c_validation": str(TERRAIN_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m8_status": m8_report.get("status"),
        "terrain_c_validation": terrain_report,
    }
    M9_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, terrain_report)
    print()
    print("M9:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
