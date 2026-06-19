#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M20: clean-room regular-cell equivalence."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M20_DIR = ROOT / "research" / "official_topology" / "m20"
M19_REPORT = (
    ROOT / "research" / "official_topology" / "m19" / "m19_report.json"
)
REGULAR_REPORT = ROOT / "validation" / "regular_cell_equivalence_report.json"
C_REPORT = M20_DIR / "m20_c_validation.json"
CORE_C_REPORT = ROOT / "validation" / "core_c_report.json"
GODOT_OUTPUT = (
    ROOT / "godot" / "validation" / "01_runtime" / "runtime_dump.json"
)
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
M20_REPORT = M20_DIR / "m20_report.json"
RESULTS = M20_DIR / "results.md"
PASS_STATUS = "PASS_M20_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE"


def stable_command(command: List[str]) -> List[str]:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    result = []
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            result.append("python")
        elif index == 0 and Path(item).name.lower() in ("godot", "godot.exe"):
            result.append("godot")
        else:
            result.append(
                item.replace(root_native, "<repo>").replace(
                    root_forward,
                    "<repo>",
                )
            )
    return result


def sanitize_output(output: str) -> str:
    return (
        output.replace(str(ROOT), "<repo>")
        .replace(str(ROOT).replace("\\", "/"), "<repo>")
        .replace(str(Path(sys.executable)), "python")
    )


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
    for name in ("godot_path.txt", "GODOT_PATH.txt"):
        path_file = ROOT / name
        if path_file.exists():
            raw = path_file.read_text(
                encoding="utf-8",
                errors="replace",
            ).strip().strip('"')
            if raw:
                candidates.append(Path(raw))
    for name in ("godot", "godot.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    candidates.extend([
        Path(
            "C:/Program Files (x86)/Steam/steamapps/common/"
            "Godot Engine/godot.exe"
        ),
        Path(
            "C:/Program Files/Steam/steamapps/common/"
            "Godot Engine/godot.exe"
        ),
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


def write_results(
    report: Dict[str, Any],
    regular_report: Dict[str, Any],
    readiness: Dict[str, Any],
) -> None:
    metrics = regular_report.get("metrics", {})
    topology = metrics.get("topology", {})
    classes = metrics.get("classes", {})
    lines = [
        "# M20 Clean-Room Regular-Cell Equivalence",
        "",
        "M20 replaces the fixed-diagonal tetrahedral regular table with a preferred-polarity modified-Marching-Cubes derivation compatible with M4.",
        "",
        f"- Status: `{report['status']}`",
        f"- M19 transition topology: `{report.get('m19_status')}`",
        f"- Python regular proof: `{regular_report.get('status')}`",
        f"- Zig C runtime proof: `{report.get('c_status')}`",
        f"- Godot regular-table runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- Readiness regular gate: `{report.get('regular_gate_status')}`",
        "",
        "## Exhaustive coverage",
        "",
        f"- Cases / behavior classes: `{topology.get('cases')}` / `{classes.get('behavior_classes')}`",
        f"- Vertices / triangles: `{topology.get('vertices')}` / `{topology.get('triangles')}`",
        f"- Maximum vertices / triangles: `{topology.get('max_vertices')}` / `{topology.get('max_triangles')}`",
        f"- Regular/regular seam comparisons: `{metrics.get('regular_neighbor_comparisons')}`",
        f"- Regular/M4 seam comparisons: `{metrics.get('regular_m4_comparisons')}`",
        f"- Failures: `{len(regular_report.get('failures', []))}`",
        "",
        "## Readiness effect",
        "",
        f"- Remaining blocking gates: `{len(readiness.get('blocking_gate_ids', []))}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "M20 proves functional regular-cell behavior. Exact regular class numbering, reuse encoding, and bytes remain separate compatibility claims.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([
            sys.executable,
            "tools/generate_regular.py",
            "--out",
            "generated",
        ]),
        run_step([sys.executable, "tools/export_transvoxel.py"]),
        run_step([sys.executable, "tools/sync_godot_tables.py"]),
        run_step([sys.executable, "tools/verify_generated_tables.py"]),
        run_step([sys.executable, "tools/validate_tables.py"]),
        run_step([sys.executable, "tools/validate_transvoxel.py"]),
        run_step([
            sys.executable,
            "tools/validate_regular_cell_equivalence.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m20/test_regular_cell_c.py",
        ]),
        run_step([sys.executable, "tools/test_core_c.py"]),
        run_step([sys.executable, "tools/test_m4_backend_c.py"]),
        run_step([sys.executable, "tools/test_m4_terrain_c.py"]),
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
        print("M20 requires actual Godot runtime; no executable found.")

    m19 = read_json(M19_REPORT)
    regular_report = read_json(REGULAR_REPORT)
    c_report = read_json(C_REPORT)
    core_c = read_json(CORE_C_REPORT)
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and m19.get("status")
        == "PASS_M19_PUBLISHED_TRANSITION_TOPOLOGY_BEHAVIOR"
        and regular_report.get("status")
        == "PASS_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE"
        and regular_report.get("functional_regular_cell_equivalence")
        == "PROVEN"
        and c_report.get("status")
        == "PASS_M20_ZIG_CLEAN_ROOM_REGULAR_CELL_RUNTIME"
        and core_c.get("status") == "PASS"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and godot_stage.get("tables", {}).get("regular_total_triangles")
        == 820
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m20.report.v1",
        "status": PASS_STATUS if base_ok else "FAIL_M20_REGULAR_CELL",
        "meaning": (
            "M20 replaces and proves the default regular-cell table using a "
            "clean-room preferred-polarity modified-Marching-Cubes derivation "
            "that is seam-compatible with M4."
        ),
        "source_reference": regular_report.get("source_reference"),
        "functional_regular_cell_equivalence": (
            "PROVEN" if base_ok else "NOT_PROVEN"
        ),
        "exact_regular_table_identity": "NOT_PROVEN",
        "default_regular_core_replaced": True,
        "m19_status": m19.get("status"),
        "regular_validation_status": regular_report.get("status"),
        "c_status": c_report.get("status"),
        "core_c_status": core_c.get("status"),
        "godot_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "metrics": regular_report.get("metrics", {}),
        "steps": steps,
        "claim_boundary": regular_report.get("claim_boundary", {}),
    }
    M20_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_step = run_step([
        sys.executable,
        "tools/m4_replacement_readiness.py",
    ])
    steps.append(readiness_step)
    readiness = read_json(READINESS)
    regular_gate = next(
        (
            gate
            for gate in readiness.get("gates", [])
            if gate.get("id") == "official_regular_cell_equivalence"
        ),
        {},
    )
    final_ok = (
        base_ok
        and readiness_step["returncode"] == 0
        and readiness.get("status")
        == "READY_M4_DEFAULT_TRANSITION_BACKEND_FUNCTIONAL_FULL_REPLACEMENT_BLOCKED"
        and regular_gate.get("status") == "PASS"
        and len(readiness.get("blocking_gate_ids", [])) == 6
        and readiness.get("next_milestone", {}).get("id")
        == "M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY"
    )
    report["status"] = (
        PASS_STATUS if final_ok else "FAIL_M20_REGULAR_CELL"
    )
    report["steps"] = steps
    report["regular_gate_status"] = regular_gate.get("status")
    report["readiness_status"] = readiness.get("status")
    report["next_milestone"] = readiness.get("next_milestone", {})
    M20_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report, regular_report, readiness)
    print()
    print("M20:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
