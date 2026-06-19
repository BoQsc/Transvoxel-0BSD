#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M24: exact regular/transition topology convergence."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M24_DIR = ROOT / "research" / "official_topology" / "m24"
REPORT = M24_DIR / "m24_report.json"
RESULTS = M24_DIR / "results.md"
TOPOLOGY_REPORT = ROOT / "validation" / "m24_exact_topology_report.json"
C_REPORT = M24_DIR / "m24_c_validation.json"
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
CLAIM_BOUNDARY = (
    ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
)
PROJECT_TRACKS = ROOT / "validation" / "project_tracks_report.json"
PASS_STATUS = "PASS_M24_EXACT_REGULAR_TRANSITION_TOPOLOGY"


def sanitize(output: str) -> str:
    return (
        output.replace(str(ROOT), "<repo>")
        .replace(str(ROOT).replace("\\", "/"), "<repo>")
        .replace(str(Path.home()), "<home>")
        .replace(str(Path.home()).replace("\\", "/"), "<home>")
        .replace(str(Path(sys.executable)), "python")
    )


def stable_command(command: List[str]) -> List[str]:
    result = []
    for index, item in enumerate(command):
        if index == 0 and Path(item) == Path(sys.executable):
            result.append("python")
        else:
            result.append(
                item.replace(str(ROOT), "<repo>")
                .replace(str(ROOT).replace("\\", "/"), "<repo>")
                .replace(str(Path.home()), "<home>")
                .replace(str(Path.home()).replace("\\", "/"), "<home>")
            )
    return result


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


def write_results(report: Dict[str, Any]) -> None:
    topology = report["topology_summary"]
    lines = [
        "# M24 Exact Topology Convergence",
        "",
        f"- Status: `{report['status']}`",
        f"- Regular oriented topology: "
        f"`{topology['regular_oriented_matches']}/256`",
        f"- Transition oriented topology: "
        f"`{topology['transition_oriented_matches']}/512`",
        f"- Zig C candidate: `{report['c_status']}`",
        f"- Existing C/C++ consumer contract: `{report['consumer_status']}`",
        f"- Remaining exact blockers: "
        f"`{len(report['readiness']['blocking_gate_ids'])}`",
        f"- Roadmap state: "
        f"`{report['readiness']['next_milestone']['id']}`",
        "",
        "M24 proves exact edge-labeled oriented topology. The exact selection "
        "data is MIT; generator code and this aggregate report are 0BSD.",
        "",
        "No zip artifact is built.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([
            sys.executable,
            "research/official_topology/m24/build_exact_topology_candidate.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m24/test_m24_candidate_c.py",
        ]),
        run_step([sys.executable, "tools/export_transvoxel.py"]),
        run_step([sys.executable, "tools/validate_transvoxel.py"]),
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
    topology = read_json(TOPOLOGY_REPORT)
    c_report = read_json(C_REPORT)
    readiness = read_json(READINESS)
    claim_boundary = read_json(CLAIM_BOUNDARY)
    project_tracks = read_json(PROJECT_TRACKS)
    consumer = read_json(
        ROOT / "validation" / "consumer_compatibility_report.json"
    )
    regular_matches = topology.get("regular", {}).get(
        "matches",
        {},
    ).get("oriented_topology")
    transition_matches = topology.get("transition", {}).get(
        "matches",
        {},
    ).get("oriented_topology")
    final_ok = (
        all(step["returncode"] == 0 for step in steps)
        and topology.get("status") == PASS_STATUS
        and topology.get("decisions", {}).get("exact_topology_identity") is True
        and regular_matches == 256
        and transition_matches == 512
        and c_report.get("status")
        == "PASS_M24_ZIG_EXACT_TOPOLOGY_CANDIDATE"
        and consumer.get("status")
        == "PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY"
        and claim_boundary.get("status")
        == "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"
        and readiness.get("next_milestone", {}).get("id")
        in {"M25_EXACT_VERTEX_ENCODING_AND_TABLE_LAYOUT", "NONE_TERMINAL"}
        and frozenset(readiness.get("blocking_gate_ids", []))
        in {
            frozenset({
                "official_class_id_mapping",
                "official_vertex_encoding_equivalence",
                "official_regular_table_identity",
                "exact_0bsd_provenance_clearance",
                "official_transvoxel_cpp_byte_identity",
            }),
            frozenset({
                "official_class_id_mapping",
                "official_regular_table_identity",
                "exact_0bsd_provenance_clearance",
                "official_transvoxel_cpp_byte_identity",
            }),
        }
        and project_tracks.get("status") == "PASS"
    )
    report = {
        "schema": "boqsc.transvoxel.official_topology.m24.report.v1",
        "report_license": "0BSD",
        "aggregate_only": True,
        "contains_exact_arrays": False,
        "status": PASS_STATUS if final_ok else "FAIL_M24_EXACT_TOPOLOGY",
        "meaning": (
            "M24 proves exact regular and transition edge-labeled oriented "
            "topology using clean-room boundary derivation and compact "
            "oracle-calibrated triangulation-selection rules."
        ),
        "topology_summary": {
            "status": topology.get("status"),
            "regular_oriented_matches": regular_matches,
            "transition_oriented_matches": transition_matches,
            "rules": topology.get("rules"),
        },
        "c_status": c_report.get("status"),
        "consumer_status": consumer.get("status"),
        "readiness": {
            "status": readiness.get("status"),
            "blocking_gate_ids": readiness.get("blocking_gate_ids", []),
            "next_milestone": readiness.get("next_milestone", {}),
        },
        "claim_boundary_status": claim_boundary.get("status"),
        "project_tracks_status": project_tracks.get("status"),
        "steps": steps,
    }
    REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report)
    print()
    print("M24:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
