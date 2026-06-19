#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M15: M4 six-face orientation validation in C and Godot."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M15_DIR = ROOT / "research" / "official_topology" / "m15"
M14_REPORT = ROOT / "research" / "official_topology" / "m14" / "m14_report.json"
C_REPORT = M15_DIR / "m15_c_validation.json"
GODOT_PROJECT_REPORT = ROOT / "validation" / "godot_project_report.json"
ORIENTATION_REPORT = ROOT / "validation" / "m4_six_face_orientation_report.json"
GODOT_OUTPUT = (
    ROOT
    / "godot"
    / "validation"
    / "11_m4_six_face_orientation"
    / "m4_six_face_orientation.json"
)
READINESS_REPORT = ROOT / "validation" / "m4_replacement_readiness_report.json"
M15_REPORT = M15_DIR / "m15_report.json"
RESULTS = M15_DIR / "results.md"
PASS_STATUS = "PASS_M15_M4_SIX_FACE_ORIENTATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN"


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


def compact_totals(data: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "faces",
        "failed_faces",
        "cases",
        "vertices",
        "triangles",
        "invalid_triangles",
        "degenerate_triangles",
        "transform_failures",
        "orientation_failures",
        "frame_failures",
        "seam_builds",
        "shared_faces",
        "seam_failures",
        "seam_vertices",
        "seam_triangles",
    ]
    return {key: data.get(key) for key in keys}


def write_results(
    report: Dict[str, Any],
    orientation: Dict[str, Any],
    readiness: Dict[str, Any],
) -> None:
    totals = orientation.get("godot_totals", {})
    lines = [
        "# M15 M4 Six-Face Orientation Validation",
        "",
        "M15 validates explicit right-handed M4 transition frames for all six axis directions in Zig-compiled C and actual Godot runtime execution.",
        "",
        f"- Status: `{report['status']}`",
        f"- M14 status: `{report.get('m14_status')}`",
        f"- C validation: `{report.get('c_status')}`",
        f"- Godot runtime executed: `{report.get('godot_runtime_executed')}`",
        f"- Combined validation: `{orientation.get('status')}`",
        "",
        "## Coverage",
        "",
        f"- Face directions: `{totals.get('faces')}`",
        f"- Exhaustive oriented case builds: `{totals.get('cases')}`",
        f"- Oriented vertices: `{totals.get('vertices')}`",
        f"- Oriented triangles: `{totals.get('triangles')}`",
        f"- Invalid triangles: `{totals.get('invalid_triangles')}`",
        f"- Degenerate triangles: `{totals.get('degenerate_triangles')}`",
        f"- Frame failures: `{totals.get('frame_failures')}`",
        f"- Transform round-trip failures: `{totals.get('transform_failures')}`",
        f"- Winding/orientation failures: `{totals.get('orientation_failures')}`",
        f"- Neighbor seam builds: `{totals.get('seam_builds')}`",
        f"- Shared side faces checked: `{totals.get('shared_faces')}`",
        f"- Seam failures: `{totals.get('seam_failures')}`",
        "",
        "## Readiness effect",
        "",
        f"- Six-face readiness gate: `{report.get('six_face_gate_status')}`",
        f"- Remaining blocking gates: `{len(readiness.get('blocking_gate_ids', []))}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "M15 proves internal six-face runtime consistency. Official reference convention and official transition topology equivalence remain `NOT_PROVEN`.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def base_report(
    *,
    status: str,
    steps: List[Dict[str, object]],
    m14: Dict[str, Any],
    c_report: Dict[str, Any],
    orientation: Dict[str, Any],
    godot_stage: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "schema": "boqsc.transvoxel.official_topology.m15.report.v1",
        "status": status,
        "meaning": (
            "M15 passes only after Zig-compiled C and actual Godot runtime "
            "validation cover all 512 M4 cases and deterministic side seams in "
            "all six explicit right-handed transition-face frames."
        ),
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "official_reference_convention_equivalence": "NOT_PROVEN",
        "official_triangle_topology_equivalence": "NOT_PROVEN",
        "default_core_replaced": False,
        "m14_status": m14.get("status"),
        "c_status": c_report.get("status"),
        "godot_project_status": read_json(GODOT_PROJECT_REPORT).get("status"),
        "godot_runtime_executed": bool(godot_stage.get("executed")),
        "godot_stage": godot_stage,
        "orientation_validation": orientation,
        "steps": steps,
        "outputs": {
            "c_validation": str(C_REPORT.relative_to(ROOT)).replace("\\", "/"),
            "combined_validation": str(ORIENTATION_REPORT.relative_to(ROOT)).replace("\\", "/"),
            "results": str(RESULTS.relative_to(ROOT)).replace("\\", "/"),
        },
    }


def main() -> int:
    remove_stale_runtime_output(GODOT_OUTPUT)
    steps = [
        run_step([sys.executable, "research/official_topology/m15/test_m4_six_faces_c.py"]),
        run_step([sys.executable, "tools/validate_godot_project.py"]),
        run_step([sys.executable, "tools/validate_m4_six_face_orientation.py"]),
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
            "res://stages/11_m4_six_face_orientation/DumpM4SixFaceOrientation.gd",
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
                "totals": compact_totals(
                    output_data.get("validation", {}).get("totals", {})
                ),
            },
        }
    else:
        print("M15 requires Godot runtime execution; no Godot executable was found.")

    steps.append(run_step([
        sys.executable,
        "tools/validate_m4_six_face_orientation.py",
        "--require-output",
    ]))

    m14 = read_json(M14_REPORT)
    c_report = read_json(C_REPORT)
    orientation = read_json(ORIENTATION_REPORT)
    godot_project = read_json(GODOT_PROJECT_REPORT)
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and m14.get("status")
        == "PASS_M14_REPLACEMENT_READINESS_GATE_BLOCKED_ON_REQUIRED_EVIDENCE"
        and c_report.get("status")
        == "PASS_M15_ZIG_M4_SIX_FACE_ORIENTATION_VALIDATION"
        and godot_project.get("status") == "PASS"
        and bool(godot_stage.get("executed"))
        and godot_stage.get("returncode") == 0
        and godot_stage.get("status") == "PASS"
        and orientation.get("status")
        == "PASS_M4_SIX_FACE_ORIENTATION_C_AND_GODOT"
    )

    report = base_report(
        status=PASS_STATUS if base_ok else "FAIL_M15_M4_SIX_FACE_ORIENTATION",
        steps=steps,
        m14=m14,
        c_report=c_report,
        orientation=orientation,
        godot_stage=godot_stage,
    )
    M15_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_step = run_step([sys.executable, "tools/m4_replacement_readiness.py"])
    steps.append(readiness_step)
    readiness = read_json(READINESS_REPORT)
    six_face_gate = next(
        (
            gate
            for gate in readiness.get("gates", [])
            if gate.get("id") == "m4_all_six_face_orientation_runtime_validation"
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
        and six_face_gate.get("status") == "PASS"
        and readiness.get("next_milestone", {}).get("id") in {
            "M16_M4_MULTI_FACE_CORNER_JUNCTION_VALIDATION",
            "M17_M4_SELECTED_PRODUCTION_GATE",
            "M18_OFFICIAL_REFERENCE_CONVENTION_VALIDATION",
        }
    )
    report["status"] = (
        PASS_STATUS if final_ok else "FAIL_M15_M4_SIX_FACE_ORIENTATION"
    )
    report["steps"] = steps
    report["six_face_gate_status"] = six_face_gate.get("status")
    report["readiness_status"] = readiness.get("status")
    report["next_milestone"] = readiness.get("next_milestone", {})
    M15_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report, orientation, readiness)
    print()
    print("M15:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
