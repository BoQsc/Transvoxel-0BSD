#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M14: explicit M4 default/full-replacement readiness decision."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M14_DIR = ROOT / "research" / "official_topology" / "m14"
M13_REPORT = ROOT / "research" / "official_topology" / "m13" / "m13_report.json"
READINESS_REPORT = ROOT / "validation" / "m4_replacement_readiness_report.json"
M14_REPORT = M14_DIR / "m14_report.json"
RESULTS = M14_DIR / "results.md"


def stable_command(command: List[str]) -> List[str]:
    out: List[str] = []
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            out.append("python")
        else:
            out.append(item.replace(root_native, "<repo>").replace(root_forward, "<repo>"))
    return out


def sanitize_output(output: str) -> str:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    return output.replace(root_native, "<repo>").replace(root_forward, "<repo>").replace(str(Path(sys.executable)), "python")


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


def readiness_summary(readiness: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": readiness.get("status"),
        "analysis_completed": readiness.get("analysis_completed"),
        "decisions": readiness.get("decisions", {}),
        "passing_gate_ids": readiness.get("passing_gate_ids", []),
        "blocking_gate_ids": readiness.get("blocking_gate_ids", []),
        "failed_gate_ids": readiness.get("failed_gate_ids", []),
        "next_milestone": readiness.get("next_milestone", {}),
        "claim_boundary": readiness.get("claim_boundary", {}),
    }


def write_results(report: Dict[str, Any], readiness: Dict[str, Any]) -> None:
    decisions = readiness.get("decisions", {})
    lines = [
        "# M14 M4 Replacement-Readiness Gate",
        "",
        "M14 makes the default/full-replacement decision explicit from current machine-readable evidence.",
        "",
        f"- Status: `{report['status']}`",
        f"- M13 status: `{report.get('m13_status')}`",
        f"- Readiness report: `{readiness.get('status')}`",
        "",
        "## Decisions",
        "",
        f"- Optional M4 transition backend candidate ready: `{decisions.get('optional_transition_backend_candidate_ready')}`",
        f"- Ready to replace default transition backend: `{decisions.get('ready_to_replace_default_transition_backend')}`",
        f"- Functional full replacement ready: `{decisions.get('functional_full_replacement_ready')}`",
        f"- Exact table-compatible replacement ready: `{decisions.get('exact_table_compatible_replacement_ready')}`",
        "",
        "## Blocking gates",
        "",
    ]
    for gate_id in readiness.get("blocking_gate_ids", []):
        lines.append(f"- `{gate_id}`")
    next_milestone = readiness.get("next_milestone", {})
    lines.extend([
        "",
        "## Next milestone",
        "",
        f"- ID: `{next_milestone.get('id')}`",
        f"- Objective: {next_milestone.get('objective')}",
        f"- Reason: {next_milestone.get('why_first')}",
        "",
        "M14 passing means the decision gate is correct and honest. It does not mean the replacement itself is proven.",
        "",
    ])
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "research/official_topology/m13/run_m13.py"]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
    ]
    m13 = read_json(M13_REPORT)
    readiness = read_json(READINESS_REPORT)
    decisions = readiness.get("decisions", {})
    ok = (
        all(step["returncode"] == 0 for step in steps)
        and m13.get("status") == "PASS_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
        and readiness.get("status") == "BLOCKED_M4_DEFAULT_REPLACEMENT_REQUIRED_EVIDENCE_NOT_PROVEN"
        and readiness.get("analysis_completed") is True
        and decisions.get("optional_transition_backend_candidate_ready") is True
        and decisions.get("ready_to_replace_default_transition_backend") is False
        and decisions.get("functional_full_replacement_ready") is False
        and len(readiness.get("blocking_gate_ids", [])) >= 7
        and readiness.get("next_milestone", {}).get("id") in {
            "M15_M4_SIX_FACE_ORIENTATION_VALIDATION",
            "M16_M4_MULTI_FACE_CORNER_JUNCTION_VALIDATION",
            "M17_M4_SELECTED_PRODUCTION_GATE",
        }
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m14.report.v1",
        "status": (
            "PASS_M14_REPLACEMENT_READINESS_GATE_BLOCKED_ON_REQUIRED_EVIDENCE"
            if ok else "FAIL_M14_REPLACEMENT_READINESS_GATE"
        ),
        "meaning": (
            "M14 passes when the readiness analysis correctly recognizes the optional "
            "M4 backend as a strong candidate while blocking default/full replacement "
            "claims until all required evidence exists."
        ),
        "m13_status": m13.get("status"),
        "readiness": readiness_summary(readiness),
        "steps": steps,
        "outputs": {
            "readiness_json": str(READINESS_REPORT.relative_to(ROOT)),
            "readiness_markdown": "validation/m4_replacement_readiness_report.md",
            "results": str(RESULTS.relative_to(ROOT)),
        },
    }
    M14_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_results(report, readiness)
    print()
    print("M14:", report["status"])
    print(RESULTS)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
