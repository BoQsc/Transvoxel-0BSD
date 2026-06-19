#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M23: verified external official-oracle baseline."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M23_DIR = ROOT / "research" / "official_topology" / "m23"
REPORT = M23_DIR / "m23_report.json"
RESULTS = M23_DIR / "results.md"
ORACLE_REPORT = ROOT / "validation" / "official_oracle_comparison_report.json"
READINESS_REPORT = ROOT / "validation" / "m4_replacement_readiness_report.json"
CLAIM_BOUNDARY_REPORT = (
    ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
)
PROJECT_TRACKS_REPORT = ROOT / "validation" / "project_tracks_report.json"
PASS_STATUS = (
    "PASS_M23_OFFICIAL_ORACLE_BASELINE_EXACT_REPLACEMENT_NOT_READY"
)


def sanitize(output: str) -> str:
    return (
        output.replace(str(ROOT), "<repo>")
        .replace(str(ROOT).replace("\\", "/"), "<repo>")
        .replace(str(Path.home()), "<home>")
        .replace(str(Path.home()).replace("\\", "/"), "<home>")
        .replace(str(Path(sys.executable)), "python")
    )


def stable_command(command: List[str]) -> List[str]:
    output = []
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            output.append("python")
        else:
            output.append(
                item.replace(str(ROOT), "<repo>")
                .replace(str(ROOT).replace("\\", "/"), "<repo>")
                .replace(str(Path.home()), "<home>")
                .replace(str(Path.home()).replace("\\", "/"), "<home>")
            )
    return output


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


def write_results(report: Dict[str, Any]) -> None:
    oracle = report["oracle_report"]
    regular = oracle["regular"]
    transition = oracle["transition"]
    lines = [
        "# M23 Official Oracle Baseline",
        "",
        f"- Status: `{report['status']}`",
        f"- Oracle verified: `{oracle['oracle']['verified']}`",
        f"- Oracle commit: `{oracle['oracle']['commit']}`",
        f"- Regular cases compared: `{regular['case_count']}`",
        f"- Regular oriented topology matches: "
        f"`{regular['matches']['oriented_topology']}`",
        f"- Transition cases compared: `{transition['case_count']}`",
        f"- Transition oriented topology matches: "
        f"`{transition['matches']['oriented_topology']}`",
        f"- Exact replacement ready: "
        f"`{oracle['decisions']['exact_replacement_ready']}`",
        f"- Next milestone: `{oracle['next_milestone']['id']}`",
        "",
        "M23 is a successful exhaustive baseline, not an exact-equivalence pass.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    M23_DIR.mkdir(parents=True, exist_ok=True)
    steps = [
        run_step([sys.executable, "tools/export_transvoxel.py"]),
        run_step([sys.executable, "tools/validate_transvoxel.py"]),
        run_step([sys.executable, "tools/test_core_c.py"]),
        run_step([sys.executable, "tools/test_consumer_compatibility.py"]),
        run_step([sys.executable, "tools/compare_official_oracle.py"]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
        run_step([
            sys.executable,
            "tools/validate_exact_compatibility_claim_boundary.py",
        ]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
        run_step([sys.executable, "tools/project_tracks_report.py"]),
    ]
    oracle = json.loads(ORACLE_REPORT.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_REPORT.read_text(encoding="utf-8"))
    claim_boundary = json.loads(
        CLAIM_BOUNDARY_REPORT.read_text(encoding="utf-8")
    )
    project_tracks = json.loads(
        PROJECT_TRACKS_REPORT.read_text(encoding="utf-8")
    )
    final_ok = (
        all(step["returncode"] == 0 for step in steps)
        and oracle.get("status") == PASS_STATUS
        and oracle.get("oracle", {}).get("verified") is True
        and oracle.get("regular", {}).get("case_count") == 256
        and oracle.get("transition", {}).get("case_count") == 512
        and oracle.get("decisions", {}).get("oracle_baseline_complete") is True
        and oracle.get("decisions", {}).get("exact_replacement_ready") is False
        and oracle.get("next_milestone", {}).get("id")
        == "M24_EXACT_TOPOLOGY_CONVERGENCE"
        and readiness.get("next_milestone", {}).get("id")
        in {"M24_EXACT_TOPOLOGY_CONVERGENCE", "NONE_TERMINAL"}
        and claim_boundary.get("status")
        == "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"
        and project_tracks.get("status") == "PASS"
    )
    report = {
        "schema": "boqsc.transvoxel.official_topology.m23.report.v1",
        "report_license": "0BSD",
        "aggregate_only": True,
        "contains_exact_arrays": False,
        "status": PASS_STATUS if final_ok else "FAIL_M23_OFFICIAL_ORACLE_BASELINE",
        "meaning": (
            "The verified external official oracle was compared against all "
            "regular and transition cases. Passing means the baseline is "
            "complete; exact replacement remains blocked by measured "
            "differences."
        ),
        "oracle_report": oracle,
        "readiness_report": readiness,
        "claim_boundary_report": claim_boundary,
        "project_tracks_report": project_tracks,
        "steps": steps,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report)
    print()
    print("M23:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
