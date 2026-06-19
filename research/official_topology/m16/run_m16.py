#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M16: mapped M4 multi-face corner-junction validation."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M16_DIR = ROOT / "research" / "official_topology" / "m16"
M4_REPORT = ROOT / "research" / "official_topology" / "m4" / "m4_report.json"
M15_REPORT = ROOT / "research" / "official_topology" / "m15" / "m15_report.json"
C_REPORT = M16_DIR / "m16_c_validation.json"
GODOT_PROJECT_REPORT = ROOT / "validation" / "godot_project_report.json"
JUNCTION_REPORT = ROOT / "validation" / "m4_corner_junction_report.json"
GODOT_OUTPUT = (
    ROOT
    / "godot"
    / "validation"
    / "12_m4_corner_junctions"
    / "m4_corner_junctions.json"
)
READINESS_REPORT = ROOT / "validation" / "m4_replacement_readiness_report.json"
M16_REPORT = M16_DIR / "m16_report.json"
RESULTS = M16_DIR / "results.md"
PASS_STATUS = (
    "PASS_M16_M4_DEFORMED_CORNER_JUNCTIONS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
)


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
            out.append(
                item.replace(root_native, "<repo>").replace(root_forward, "<repo>")
            )
    return out


def sanitize_output(output: str) -> str:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    return (
        output.replace(root_native, "<repo>")
        .replace(root_forward, "<repo>")
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


def remove_stale_runtime_output(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def find_godot() -> Path | None:
    candidates: List[Path] = []
    env = os.environ.get("GODOT_EXE", "").strip().strip('"')
    if env:
        candidates.append(Path(env))
    for name in ["godot_path.txt", "GODOT_PATH.txt"]:
        path_file = ROOT / name
        if path_file.exists():
            raw = path_file.read_text(
                encoding="utf-8", errors="replace"
            ).strip().strip('"')
            if raw:
                candidates.append(Path(raw))
    for name in ["godot", "godot.exe"]:
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


def write_results(
    report: Dict[str, Any],
    junction: Dict[str, Any],
    readiness: Dict[str, Any],
) -> None:
    metrics = junction.get("godot_metrics", {})
    lines = [
        "# M16 M4 Deformed Corner-Junction Validation",
        "",
        "M16 validates mapped non-box M4 transition cells where three perpendicular LOD faces meet.",
        "",
        f"- Status: `{report['status']}`",
        f"- M4 status: `{report.get('m4_status')}`",
        f"- M15 status: `{report.get('m15_status')}`",
        f"- C validation: `{report.get('c_status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- Combined validation: `{junction.get('status')}`",
        "",
        "## Coverage",
        "",
        f"- Signed corner octants: `{metrics.get('octants')}`",
        f"- Junction scenarios: `{metrics.get('junctions')}`",
        f"- Mapped transition-cell builds: `{metrics.get('builds')}`",
        f"- Shared lateral faces: `{metrics.get('shared_faces')}`",
        f"- Nonempty shared lateral faces: `{metrics.get('nonempty_shared_faces')}`",
        f"- Shared sample comparisons: `{metrics.get('shared_samples')}`",
        f"- Triangles: `{metrics.get('triangles')}`",
        f"- Invalid/degenerate triangles: `{metrics.get('invalid_triangles')}` / `{metrics.get('degenerate_triangles')}`",
        f"- Internal winding failures: `{metrics.get('internal_winding_failures')}`",
        f"- Lateral geometry failures: `{metrics.get('lateral_geometry_failures')}`",
        f"- Lateral winding failures: `{metrics.get('lateral_winding_failures')}`",
        f"- Corner position/value failures: `{metrics.get('corner_position_failures')}` / `{metrics.get('corner_value_failures')}`",
        "",
        "## Readiness effect",
        "",
        f"- M4 corner-junction gate: `{report.get('junction_gate_status')}`",
        f"- Remaining blocking gates: `{len(readiness.get('blocking_gate_ids', []))}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "The geometry and winding rules are independently derived from the public transition-cell description. Official table/class/topology equivalence remains `NOT_PROVEN`.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    remove_stale_runtime_output(GODOT_OUTPUT)
    steps = [
        run_step([sys.executable, "research/official_topology/m4/run_m4.py"]),
        run_step([sys.executable, "research/official_topology/m15/run_m15.py"]),
        run_step([sys.executable, "research/official_topology/m16/test_m4_corner_junctions_c.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_m4_corner_junctions.py"]),
    ]

    godot = find_godot()
    godot_stage: Dict[str, Any] = {
        "status": "NOT_RUN_GODOT_NOT_FOUND",
        "executed": False,
        "output": None,
    }
    if godot is not None:
        godot_step = run_step([
            str(godot),
            "--headless",
            "--path",
            "godot",
            "--script",
            "res://stages/12_m4_corner_junctions/DumpM4CornerJunctions.gd",
        ])
        steps.append(godot_step)
        output_data: Dict[str, Any] = {}
        if GODOT_OUTPUT.exists():
            output_data = read_json(GODOT_OUTPUT)
        godot_stage = {
            "status": output_data.get("status", "FAIL_MISSING_OUTPUT"),
            "executed": True,
            "returncode": godot_step["returncode"],
            "output_path": str(GODOT_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
            "output_summary": {
                "schema": output_data.get("schema"),
                "status": output_data.get("status"),
                "totals": output_data.get("validation", {}).get("totals", {}),
                "mesh": output_data.get("validation", {}).get("mesh", {}),
            },
        }
    else:
        print("M16 requires Godot runtime execution; no Godot executable was found.")

    steps.append(run_step([
        sys.executable,
        "tools/validate_m4_corner_junctions.py",
        "--require-output",
    ]))

    m4 = read_json(M4_REPORT)
    m15 = read_json(M15_REPORT)
    c_report = read_json(C_REPORT)
    godot_project = read_json(GODOT_PROJECT_REPORT)
    junction = read_json(JUNCTION_REPORT)
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and m4.get("status")
        == "PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and m15.get("status")
        == "PASS_M15_M4_SIX_FACE_ORIENTATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and c_report.get("status")
        == "PASS_M16_ZIG_M4_DEFORMED_CORNER_JUNCTIONS"
        and godot_project.get("status") == "PASS"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and junction.get("status")
        == "PASS_M4_DEFORMED_CORNER_JUNCTIONS_C_AND_GODOT"
    )

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m16.report.v1",
        "status": PASS_STATUS if base_ok else "FAIL_M16_M4_CORNER_JUNCTIONS",
        "meaning": (
            "M16 passes only after clean-room M4 winding validation plus "
            "Zig-compiled C and actual Godot runtime validation of mapped "
            "three-face corner junctions in all eight signed octants."
        ),
        "source_reference": {
            "title": "Voxel-Based Terrain for Real-Time Virtual Simulations",
            "author": "Eric Lengyel",
            "url": "https://transvoxel.org/Lengyel-VoxelTerrain.pdf",
            "relevant_sections": [
                "Section 4.3 transition-cell geometry and coincident lateral faces",
                "Figure 4.9 multiple transition cells",
                "Section 4.4 boundary-cell deformation",
            ],
            "use_boundary": (
                "Used only for public geometric/algorithmic constraints. No "
                "official lookup-table arrays or values were read or compared."
            ),
        },
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_reference_convention_equivalence": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "m4_status": m4.get("status"),
        "m15_status": m15.get("status"),
        "c_status": c_report.get("status"),
        "godot_project_status": godot_project.get("status"),
        "godot_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "junction_validation": junction,
        "steps": steps,
        "outputs": {
            "c_validation": str(C_REPORT.relative_to(ROOT)).replace("\\", "/"),
            "combined_validation": str(JUNCTION_REPORT.relative_to(ROOT)).replace("\\", "/"),
            "results": str(RESULTS.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    M16_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_step = run_step([sys.executable, "tools/m4_replacement_readiness.py"])
    steps.append(readiness_step)
    readiness = read_json(READINESS_REPORT)
    junction_gate = next(
        (
            gate
            for gate in readiness.get("gates", [])
            if gate.get("id") == "m4_multi_face_corner_junction_validation"
        ),
        {},
    )
    final_ok = (
        base_ok
        and readiness_step["returncode"] == 0
        and readiness.get("status") in {
            "BLOCKED_M4_DEFAULT_REPLACEMENT_REQUIRED_EVIDENCE_NOT_PROVEN",
            "READY_M4_DEFAULT_TRANSITION_BACKEND_FUNCTIONAL_FULL_REPLACEMENT_BLOCKED",
        }
        and junction_gate.get("status") == "PASS"
        and readiness.get("next_milestone", {}).get("id") in {
            "M17_M4_SELECTED_PRODUCTION_GATE",
            "M18_OFFICIAL_REFERENCE_CONVENTION_VALIDATION",
        }
    )
    report["status"] = (
        PASS_STATUS if final_ok else "FAIL_M16_M4_CORNER_JUNCTIONS"
    )
    report["steps"] = steps
    report["junction_gate_status"] = junction_gate.get("status")
    report["readiness_status"] = readiness.get("status")
    report["next_milestone"] = readiness.get("next_milestone", {})
    M16_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report, junction, readiness)
    print()
    print("M16:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
