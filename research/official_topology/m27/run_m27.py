#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M27: terminal exact-0BSD topology/provenance decision."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M27_DIR = ROOT / "research" / "official_topology" / "m27"
AUDIT = M27_DIR / "m27_terminal_audit.json"
REPORT = M27_DIR / "m27_report.json"
RESULTS = M27_DIR / "results.md"
VALIDATION_JSON = ROOT / "validation" / "m27_terminal_roadmap_report.json"
VALIDATION_MD = ROOT / "validation" / "m27_terminal_roadmap_report.md"
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
CLAIM_BOUNDARY = (
    ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
)
PROJECT_TRACKS = ROOT / "validation" / "project_tracks_report.json"
TERMINAL_STATUS = "TERMINAL_M27_EXACT_0BSD_REPLACEMENT_NOT_ACHIEVED"


def sanitize(output: str) -> str:
    return (
        output.replace(str(ROOT), "<repo>")
        .replace(str(ROOT).replace("\\", "/"), "<repo>")
        .replace(str(Path.home()), "<home>")
        .replace(str(Path.home()).replace("\\", "/"), "<home>")
        .replace(str(Path(sys.executable)), "python")
    )


def stable_command(command: List[str]) -> List[str]:
    return [
        (
            "python"
            if index == 0 and Path(item) == Path(sys.executable)
            else item.replace(str(ROOT), "<repo>")
            .replace(str(ROOT).replace("\\", "/"), "<repo>")
            .replace(str(Path.home()), "<home>")
            .replace(str(Path.home()).replace("\\", "/"), "<home>")
        )
        for index, item in enumerate(command)
    ]


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


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    audit = report["terminal_audit"]
    independent = audit["independent_0bsd_rule"]
    exact = audit["oracle_calibrated_exact_candidate"]
    lines = [
        "# M27 Terminal Exact-0BSD Decision",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- Exact 0BSD goal achieved: `{report['exact_0bsd_goal_achieved']}`",
        f"- Technical exact integration proven: `{report['technical_semantic_integration_proven']}`",
        f"- Independent regular exact matches: `{independent['regular_oriented_topology_matches']}/256`",
        f"- Independent transition exact matches: `{independent['transition_oriented_topology_matches']}/512`",
        f"- Oracle-calibrated regular exact matches: `{exact['regular_oriented_topology_matches']}/256`",
        f"- Oracle-calibrated transition exact matches: `{exact['transition_oriented_topology_matches']}/512`",
        f"- M24 regular rules with nonzero oracle selection: `{exact['regular_rules_with_nonzero_oracle_option']}`",
        f"- M24 transition representative rules with nonzero oracle selection: `{exact['transition_rules_with_nonzero_oracle_option']}`",
        f"- Roadmap terminal: `{report['terminal']}`",
        f"- Next milestone: `{report['next_milestone']['id']}`",
        "",
        "The published rules constrain robust boundary connectivity but permit "
        "multiple legal interior triangulations. The independent deterministic "
        "0BSD rule therefore does not reproduce every authored official "
        "interior. The exact M24-M26 candidate is technically proven, but it "
        "depends on selections calibrated against the MIT implementation and "
        "is not cleared for an 0BSD release.",
        "",
        "Terminal choices are: retain MIT for exact compatibility, use the "
        "functional non-exact 0BSD core, or obtain explicit permission. There "
        "is no automatic M28.",
        "",
        "This is an engineering provenance decision, not legal advice.",
        "",
        "No zip artifact is built.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([sys.executable, "tools/generate_regular.py", "--out", "generated"]),
        run_step([
            sys.executable,
            "research/official_topology/m4/generate_runtime_tables.py",
            "--out",
            "generated",
        ]),
        run_step([sys.executable, "tools/export_transvoxel.py"]),
        run_step([sys.executable, "tools/validate_transvoxel.py"]),
        run_step([sys.executable, "tools/compare_official_oracle.py"]),
        run_step([
            sys.executable,
            "research/official_topology/m24/build_exact_topology_candidate.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m25/build_compatible_transvoxel_cpp.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m25/test_original_contract_consumer.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m26/build_godot_voxel_replacement.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m26/test_godot_voxel_integration.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m26/test_full_godot_voxel_build.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m27/terminal_audit.py",
        ]),
        run_step([sys.executable, "tools/test_core_c.py"]),
        run_step([sys.executable, "tools/test_consumer_compatibility.py"]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
        run_step([
            sys.executable,
            "tools/validate_exact_compatibility_claim_boundary.py",
        ]),
        run_step([sys.executable, "tools/m4_replacement_readiness.py"]),
        run_step([sys.executable, "tools/project_tracks_report.py"]),
    ]
    audit = read_json(AUDIT)
    readiness = read_json(READINESS)
    claim_boundary = read_json(CLAIM_BOUNDARY)
    project_tracks = read_json(PROJECT_TRACKS)
    final_ok = (
        all(step["returncode"] == 0 for step in steps)
        and audit.get("status") == TERMINAL_STATUS
        and audit.get("decision", {}).get("exact_0bsd_goal_achieved") is False
        and audit.get("decision", {}).get(
            "technical_semantic_integration_proven"
        )
        is True
        and audit.get("decision", {}).get("no_further_automatic_milestones")
        is True
        and readiness.get("status")
        == "TERMINAL_EXACT_0BSD_TRANSVOXEL_CPP_REPLACEMENT_NOT_ACHIEVED"
        and readiness.get("decisions", {}).get("terminal_exact_0bsd_outcome")
        is True
        and readiness.get("next_milestone", {}).get("id") == "NONE_TERMINAL"
        and claim_boundary.get("status")
        == "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"
        and project_tracks.get("status") == "PASS"
        and project_tracks.get("tracks", {})
        .get("official_topology_research", {})
        .get("status")
        == "TERMINAL_NOT_ACHIEVED"
    )
    report = {
        "schema": "boqsc.transvoxel.official_topology.m27.report.v1",
        "status": TERMINAL_STATUS if final_ok else "FAIL_M27_TERMINAL_MILESTONE",
        "terminal": final_ok,
        "exact_0bsd_goal_achieved": False,
        "technical_semantic_integration_proven": audit.get("decision", {}).get(
            "technical_semantic_integration_proven"
        ),
        "meaning": audit.get("meaning"),
        "terminal_audit": audit,
        "readiness_status": readiness.get("status"),
        "claim_boundary_status": claim_boundary.get("status"),
        "project_tracks_status": project_tracks.get("status"),
        "next_milestone": readiness.get("next_milestone", {}),
        "steps": steps,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    REPORT.write_text(encoded, encoding="utf-8")
    VALIDATION_JSON.write_text(encoded, encoding="utf-8")
    write_markdown(report, RESULTS)
    write_markdown(report, VALIDATION_MD)
    print()
    print("M27:", report["status"])
    print("next milestone:", report["next_milestone"].get("id"))
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
