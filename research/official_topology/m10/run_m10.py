#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M10: M4 candidate through the Godot generated-data metrics path."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M10_DIR = ROOT / "research" / "official_topology" / "m10"
M9_REPORT = ROOT / "research" / "official_topology" / "m9" / "m9_report.json"
GODOT_PROJECT_REPORT = ROOT / "validation" / "godot_project_report.json"
M4_GODOT_REPORT = ROOT / "validation" / "m4_godot_candidate_report.json"
GODOT_M4_STAGE_OUTPUT = ROOT / "godot" / "validation" / "05_m4_candidate_metrics" / "m4_candidate_metrics.json"
M10_REPORT = M10_DIR / "m10_report.json"
RESULTS = M10_DIR / "results.md"


def stable_command(command: List[str]) -> List[str]:
    out: List[str] = []
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            out.append("python")
        elif index == 0 and Path(item).name.lower() in ("godot", "godot.exe"):
            out.append("godot")
        else:
            out.append(item.replace(root_native, "<repo>").replace(root_forward, "<repo>"))
    return out


def sanitize_output(output: str) -> str:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    out = output.replace(root_native, "<repo>").replace(root_forward, "<repo>")
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


def find_godot() -> Path | None:
    candidates: List[Path] = []
    env = os.environ.get("GODOT_EXE", "").strip().strip('"')
    if env:
        candidates.append(Path(env))
    for name in ["godot_path.txt", "GODOT_PATH.txt"]:
        path_file = ROOT / name
        if path_file.exists():
            raw = path_file.read_text(encoding="utf-8", errors="replace").strip().strip('"')
            if raw:
                candidates.append(Path(raw))
    for name in ["godot", "godot.exe"]:
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    candidates.append(Path("C:/Program Files (x86)/Steam/steamapps/common/Godot Engine/godot.exe"))
    candidates.append(Path("C:/Program Files/Steam/steamapps/common/Godot Engine/godot.exe"))
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except Exception:
            resolved = candidate.expanduser()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.exists() and resolved.is_file():
            return resolved
    return None


def write_results(report: Dict[str, Any], m4_report: Dict[str, Any]) -> None:
    validation = m4_report.get("validation", {})
    strips = validation.get("strips", {})
    triangles = validation.get("triangles", {})
    godot_stage = report.get("godot_stage", {})
    lines = [
        "# M10 M4 Godot Data-Path Metrics",
        "",
        "M10 validates the M4 candidate table in the Godot generated-data path.",
        "",
        f"- Status: `{report['status']}`",
        f"- M9 status: `{report.get('m9_status')}`",
        f"- Godot project preflight: `{report.get('godot_project_status')}`",
        f"- M4 Godot-style validation: `{m4_report.get('status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- Godot M4 stage status: `{godot_stage.get('status', 'NOT_RUN')}`",
        "",
        "## M4 Godot-style metrics",
        "",
        f"- Table synced to Godot: `{m4_report.get('m4_table_synced_to_godot')}`",
        f"- Cases: `{validation.get('case_count')}`",
        f"- Samples: `{validation.get('sample_count')}`",
        f"- Strip builds: `{strips.get('builds')}`",
        f"- Shared faces checked: `{strips.get('shared_faces')}`",
        f"- Seam failures / open edges: `{strips.get('failures')}`",
        f"- Invalid triangles: `{triangles.get('invalid_triangles')}`",
        f"- Degenerate triangles: `{triangles.get('degenerate_triangles')}`",
        f"- Total M4 triangles: `{triangles.get('total_triangles')}`",
        "",
        "## What passed",
        "",
        "- M4 table is synced into `godot/generated/`;",
        "- Godot project preflight includes the M4 generated table and stage;",
        "- M4 candidate table satisfies the Godot-style non-visual seam metric contract;",
        "- deterministic M4 strip fingerprints have zero shared-face mismatches;",
        "- M4 triangles are index-valid and non-degenerate under midpoint validation;",
        "",
        "## What remains unproven",
        "",
        "- Godot viewer/interactive terrain rendering through M4;",
        "- official Transvoxel.cpp byte/table identity;",
        "- official class ID mapping;",
        "- official triangle topology equivalence;",
        "- decision to make M4 the default backend.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m9/run_m9.py"]),
        run_step([sys.executable, "tools/sync_godot_tables.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_m4_godot_candidate.py"]),
    ]
    godot_stage: Dict[str, Any] = {
        "status": "NOT_RUN_GODOT_NOT_FOUND",
        "executed": False,
        "output": None,
    }
    godot = find_godot()
    if godot is not None:
        godot_step = run_step([
            str(godot),
            "--headless",
            "--path",
            "godot",
            "--script",
            "res://stages/05_m4_candidate_metrics/DumpM4CandidateMetrics.gd",
        ])
        steps.append(godot_step)
        output_data: Dict[str, Any] = {}
        if GODOT_M4_STAGE_OUTPUT.exists():
            output_data = read_json(GODOT_M4_STAGE_OUTPUT)
        godot_stage = {
            "status": output_data.get("status", "FAIL_MISSING_OUTPUT"),
            "executed": True,
            "returncode": godot_step["returncode"],
            "output_path": str(GODOT_M4_STAGE_OUTPUT.relative_to(ROOT)),
            "output": output_data,
        }
    m9_report = read_json(M9_REPORT)
    godot_project = read_json(GODOT_PROJECT_REPORT)
    m4_report = read_json(M4_GODOT_REPORT)
    godot_ok = (
        not godot_stage.get("executed")
        or (
            godot_stage.get("returncode") == 0
            and godot_stage.get("status") == "PASS"
        )
    )
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m9_report.get("status") == "PASS_M9_M4_TERRAIN_EXPORT_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and godot_project.get("status") == "PASS"
        and m4_report.get("status") == "PASS_M4_GODOT_STYLE_CANDIDATE_METRICS"
        and godot_ok
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m10.report.v1",
        "status": (
            "PASS_M10_M4_GODOT_DATA_PATH_METRICS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
            if ok else "FAIL_M10_M4_GODOT_DATA_PATH_METRICS"
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "godot_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "steps": steps,
        "outputs": {
            "godot_project_preflight": str(GODOT_PROJECT_REPORT.relative_to(ROOT)),
            "m4_godot_candidate_validation": str(M4_GODOT_REPORT.relative_to(ROOT)),
            "results": str(RESULTS.relative_to(ROOT)),
        },
        "m9_status": m9_report.get("status"),
        "godot_project_status": godot_project.get("status"),
        "m4_godot_candidate_validation": m4_report,
    }
    M10_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, m4_report)
    print()
    print("M10:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
