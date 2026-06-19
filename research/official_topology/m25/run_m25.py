#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M25: compatible Transvoxel.cpp encoding/layout research."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M25_DIR = ROOT / "research" / "official_topology" / "m25"
REPORT = M25_DIR / "m25_report.json"
RESULTS = M25_DIR / "results.md"
LAYOUT_REPORT = ROOT / "validation" / "m25_compatible_layout_report.json"
CONSUMER_REPORT = M25_DIR / "m25_consumer_validation.json"
M24_REPORT = ROOT / "validation" / "m24_exact_topology_report.json"
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
CLAIM_BOUNDARY = (
    ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
)
PROJECT_TRACKS = ROOT / "validation" / "project_tracks_report.json"
PASS_STATUS = "PASS_M25_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT"


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
    metrics = report["layout_metrics"]
    lines = [
        "# M25 Compatible Transvoxel.cpp Layout",
        "",
        f"- Status: `{report['status']}`",
        f"- Regular classes used/capacity: "
        f"`{metrics['regular_used_classes']}/16`",
        f"- Transition classes used/capacity: "
        f"`{metrics['transition_used_classes']}/56`",
        f"- Packed vertex-code case matches: "
        f"`{metrics['packed_vertex_code_multiset_matches']}/768`",
        f"- Original-contract C++ consumer: `{report['consumer_status']}`",
        f"- Remaining exact blockers: "
        f"`{len(report['readiness']['blocking_gate_ids'])}`",
        f"- Next milestone: "
        f"`{report['readiness']['next_milestone']['id']}`",
        "",
        "M25 proves compatible original data symbols, array capacities, exact "
        "topology, and packed reuse semantics with independent internal class "
        "IDs. It does not prove byte identity or release provenance.",
        "",
        "No zip artifact is built.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([
            sys.executable,
            (
                "research/official_topology/m25/"
                "build_compatible_transvoxel_cpp.py"
            ),
        ]),
        run_step([
            sys.executable,
            (
                "research/official_topology/m25/"
                "test_original_contract_consumer.py"
            ),
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
    layout = read_json(LAYOUT_REPORT)
    consumer = read_json(CONSUMER_REPORT)
    m24 = read_json(M24_REPORT)
    readiness = read_json(READINESS)
    claim_boundary = read_json(CLAIM_BOUNDARY)
    project_tracks = read_json(PROJECT_TRACKS)
    blockers = set(readiness.get("blocking_gate_ids", []))
    final_ok = (
        all(step["returncode"] == 0 for step in steps)
        and layout.get("status") == PASS_STATUS
        and layout.get("decisions", {}).get(
            "compatible_struct_and_symbol_surface"
        )
        is True
        and layout.get("decisions", {}).get(
            "packed_vertex_reuse_semantics"
        )
        is True
        and consumer.get("status")
        == "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER"
        and m24.get("status")
        == "PASS_M24_EXACT_REGULAR_TRANSITION_TOPOLOGY"
        and readiness.get("next_milestone", {}).get("id")
        in {
            "M26_REAL_ENGINE_INTEGRATION_AND_PROVENANCE",
            "M27_INDEPENDENT_EXACT_TOPOLOGY_PROVENANCE",
        }
        and blockers
        == {
            "official_class_id_mapping",
            "official_regular_table_identity",
            "exact_0bsd_provenance_clearance",
            "official_transvoxel_cpp_byte_identity",
        }
        and claim_boundary.get("status")
        == "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"
        and project_tracks.get("status") == "PASS"
    )
    report = {
        "schema": "boqsc.transvoxel.official_topology.m25.report.v1",
        "status": PASS_STATUS if final_ok else "FAIL_M25_COMPATIBLE_LAYOUT",
        "meaning": (
            "M25 generates and validates a research-only original "
            "Transvoxel.cpp data ABI surface with independent class IDs, "
            "exact topology, and formula-derived reuse codes."
        ),
        "layout_metrics": layout.get("metrics", {}),
        "consumer_status": consumer.get("status"),
        "m24_status": m24.get("status"),
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
    print("M25:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
