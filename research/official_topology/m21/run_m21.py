#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M21: default clean-room M4 transition and consumer compatibility."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M21_DIR = ROOT / "research" / "official_topology" / "m21"
REPORT = M21_DIR / "m21_report.json"
RESULTS = M21_DIR / "results.md"
PASS_STATUS = "PASS_M21_DEFAULT_M4_FUNCTIONAL_CONSUMER_COMPATIBILITY"

TRANSVOXEL_REPORT = ROOT / "validation" / "transvoxel_report.json"
CORE_C_REPORT = ROOT / "validation" / "core_c_report.json"
M4_BACKEND_REPORT = ROOT / "validation" / "m4_backend_c_report.json"
M4_TERRAIN_REPORT = ROOT / "validation" / "m4_terrain_c_report.json"
CONSUMER_REPORT = ROOT / "validation" / "consumer_compatibility_report.json"
READINESS_REPORT = ROOT / "validation" / "m4_replacement_readiness_report.json"
GODOT_OUTPUT = ROOT / "godot" / "validation" / "01_runtime" / "runtime_dump.json"


def sanitize(output: str) -> str:
    return (
        output.replace(str(ROOT), "<repo>")
        .replace(str(ROOT).replace("\\", "/"), "<repo>")
        .replace(str(Path(sys.executable)), "python")
    )


def stable_command(command: List[str]) -> List[str]:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    out: List[str] = []
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            out.append("python")
        elif index == 0 and Path(item).name.lower() in ("godot", "godot.exe"):
            out.append("godot")
        else:
            out.append(item.replace(root_native, "<repo>").replace(root_forward, "<repo>"))
    return out


def run_step(command: List[str]) -> Dict[str, Any]:
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
        "output": sanitize(proc.stdout),
    }


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_godot() -> Path | None:
    candidates: List[Path] = []
    env = os.environ.get("GODOT_EXE", "").strip().strip('"')
    if env:
        candidates.append(Path(env))
    for name in ("godot_path.txt", "GODOT_PATH.txt"):
        path_file = ROOT / name
        if path_file.exists():
            raw = path_file.read_text(encoding="utf-8", errors="replace").strip().strip('"')
            if raw:
                candidates.append(Path(raw))
    for name in ("godot", "godot.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    candidates.extend([
        Path("C:/Program Files (x86)/Steam/steamapps/common/Godot Engine/godot.exe"),
        Path("C:/Program Files/Steam/steamapps/common/Godot Engine/godot.exe"),
    ])
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


def write_results(report: Dict[str, Any]) -> None:
    consumer = report.get("consumer_report", {})
    metrics = consumer.get("metrics", {})
    readiness = report.get("readiness_report", {})
    lines = [
        "# M21 Default M4 Functional Consumer Compatibility",
        "",
        "M21 switches the public default transition export to the clean-room M4 published-topology table and proves the functional C/C++ consumer contract.",
        "",
        f"- Status: `{report['status']}`",
        f"- Transvoxel export validation: `{report.get('transvoxel_ok')}`",
        f"- Core C examples: `{report.get('core_c_status')}`",
        f"- M4 callback adapter package: `{report.get('m4_backend_status')}`",
        f"- Terrain default/adapter export: `{report.get('m4_terrain_status')}`",
        f"- Consumer compatibility: `{consumer.get('status')}`",
        f"- Readiness: `{readiness.get('status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        "",
        "## Default transition metrics",
        "",
        f"- Cases: `{metrics.get('cases')}`",
        f"- Vertices / triangles: `{metrics.get('default_vertices')}` / `{metrics.get('default_triangles')}`",
        f"- Max vertices / triangles: `{metrics.get('max_vertices')}` / `{metrics.get('max_triangles')}`",
        f"- M4 direct matches: `{metrics.get('m4_matches')}`",
        f"- Sample 13 ignored checks: `{metrics.get('sample13_ignored')}`",
        "",
        "## Claim boundary",
        "",
        f"- Allowed now: {readiness.get('claim_boundary', {}).get('allowed_now')}",
        f"- Not allowed now: {readiness.get('claim_boundary', {}).get('not_allowed_now')}",
        "",
        "No zip/package artifact is built by this milestone runner.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    M21_DIR.mkdir(parents=True, exist_ok=True)
    steps = [
        run_step([sys.executable, "tools/export_transvoxel.py"]),
        run_step([sys.executable, "tools/sync_godot_tables.py"]),
        run_step([sys.executable, "tools/validate_transvoxel.py"]),
        run_step([sys.executable, "tools/test_core_c.py"]),
        run_step([sys.executable, "tools/test_m4_backend_c.py"]),
        run_step([sys.executable, "tools/test_m4_terrain_c.py"]),
        run_step([sys.executable, "tools/test_consumer_compatibility.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
    ]

    godot = find_godot()
    godot_stage: Dict[str, Any] = {
        "executed": False,
        "status": "NOT_RUN_GODOT_NOT_FOUND",
    }
    if godot is not None:
        godot_step = run_step([
            str(godot),
            "--headless",
            "--path",
            "godot",
            "--script",
            "res://stages/01_runtime/DumpRuntimeData.gd",
        ])
        steps.append(godot_step)
        output = read_json(GODOT_OUTPUT) if GODOT_OUTPUT.exists() else {}
        godot_stage = {
            "executed": True,
            "returncode": godot_step["returncode"],
            "status": output.get("status", "MISSING_OUTPUT"),
            "tables": output.get("tables", {}),
        }
    else:
        print("M21 requires actual Godot runtime validation; no executable found.")

    readiness_step = run_step([sys.executable, "tools/m4_replacement_readiness.py"])
    steps.append(readiness_step)

    transvoxel = read_json(TRANSVOXEL_REPORT)
    core_c = read_json(CORE_C_REPORT)
    m4_backend = read_json(M4_BACKEND_REPORT)
    m4_terrain = read_json(M4_TERRAIN_REPORT)
    consumer = read_json(CONSUMER_REPORT)
    readiness = read_json(READINESS_REPORT)

    source_tables = read_json(ROOT / "generated" / "transvoxel_tables.json").get("source_tables", {})
    trans_table = read_json(ROOT / "generated" / "transvoxel_tables.json").get("transition", {})
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and transvoxel.get("ok") is True
        and source_tables.get("transition_source")
        == "generated/official_topology_candidate_tables.json"
        and len(trans_table.get("vertex_refs", [])) == 4096
        and len(trans_table.get("triangles", [])) == 2640
        and int(trans_table.get("max_vertex_count", 0)) == 12
        and int(trans_table.get("max_triangle_count", 0)) == 12
        and core_c.get("status") == "PASS"
        and m4_backend.get("status") == "PASS_M4_BACKEND_PACKAGE_C_EXAMPLE"
        and m4_backend.get("default_core_replaced") is True
        and m4_terrain.get("status") == "PASS_M4_TERRAIN_NORMAL_API_EXPORT"
        and m4_terrain.get("default_core_replaced") is True
        and consumer.get("status") == "PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY"
        and consumer.get("functional_transvoxel_cpp_consumer_compatibility") == "PROVEN"
        and readiness_step["returncode"] == 0
        and readiness.get("status")
        == "READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_EXACT_COMPATIBILITY_BLOCKED"
        and readiness.get("decisions", {}).get("functional_full_replacement_ready") is True
        and len(readiness.get("blocking_gate_ids", [])) == 5
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and godot_stage.get("tables", {}).get("transvoxel_transition_source")
        == "generated/official_topology_candidate_tables.json"
        and int(godot_stage.get("tables", {}).get("transvoxel_transition_triangles", 0)) == 2640
    )

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m21.report.v1",
        "status": PASS_STATUS if base_ok else "FAIL_M21_DEFAULT_M4_FUNCTIONAL_CONSUMER_COMPATIBILITY",
        "meaning": (
            "M21 selects the clean-room M4 transition source as the default "
            "public transition table and proves the functional C/C++ consumer "
            "compatibility contract. Exact official table-layout and byte "
            "identity remain unclaimed."
        ),
        "default_transition_source": source_tables.get("transition_source"),
        "functional_transvoxel_cpp_replacement": "PROVEN" if base_ok else "NOT_PROVEN",
        "exact_table_compatible_replacement": "NOT_PROVEN",
        "transvoxel_ok": transvoxel.get("ok"),
        "core_c_status": core_c.get("status"),
        "m4_backend_status": m4_backend.get("status"),
        "m4_terrain_status": m4_terrain.get("status"),
        "consumer_report": consumer,
        "readiness_report": readiness,
        "godot_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "steps": steps,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report)
    print()
    print("M21:", report["status"])
    print(RESULTS)
    return 0 if base_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
