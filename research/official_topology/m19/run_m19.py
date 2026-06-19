#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M19: published transition-topology behavior proof."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M19_DIR = ROOT / "research" / "official_topology" / "m19"
M18_REPORT = (
    ROOT / "research" / "official_topology" / "m18" / "m18_report.json"
)
TOPOLOGY_REPORT = (
    ROOT / "validation" / "published_transition_topology_report.json"
)
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
M19_REPORT = M19_DIR / "m19_report.json"
RESULTS = M19_DIR / "results.md"
PASS_STATUS = "PASS_M19_PUBLISHED_TRANSITION_TOPOLOGY_BEHAVIOR"


def stable_command(command: List[str]) -> List[str]:
    root_native = str(ROOT)
    root_forward = root_native.replace("\\", "/")
    return [
        (
            "python"
            if index == 0 and Path(item) == Path(sys.executable)
            else item.replace(root_native, "<repo>").replace(
                root_forward,
                "<repo>",
            )
        )
        for index, item in enumerate(command)
    ]


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


def write_results(
    report: Dict[str, Any],
    topology: Dict[str, Any],
    readiness: Dict[str, Any],
) -> None:
    metrics = topology.get("metrics", {})
    class_metrics = metrics.get("class_partition", {})
    lines = [
        "# M19 Published Transition-Topology Behavior",
        "",
        "M19 proves the clean-room M3/M4 transition candidate satisfies the published topology rules required for functional behavior.",
        "",
        f"- Status: `{report['status']}`",
        f"- M18 reference convention: `{report.get('m18_status')}`",
        f"- Topology validation: `{topology.get('status')}`",
        f"- Readiness topology gate: `{report.get('topology_gate_status')}`",
        "",
        "## Exhaustive coverage",
        "",
        f"- Cases: `{metrics.get('cases')}`",
        f"- Clean-room behavior classes: `{class_metrics.get('classes')}`",
        f"- Full/half/lateral face checks: `{metrics.get('full_face_quadrant_checks')}` / `{metrics.get('half_face_checks')}` / `{metrics.get('lateral_face_checks')}`",
        f"- Boundary loops: `{metrics.get('boundary_loops')}`",
        f"- Surface components: `{metrics.get('surface_components')}`",
        f"- Candidate triangles: `{metrics.get('triangles')}`",
        f"- Topology failures: `{metrics.get('topology_case_failures')}`",
        "",
        "## Readiness effect",
        "",
        f"- Remaining blocking gates: `{len(readiness.get('blocking_gate_ids', []))}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "M19 proves published transition topology behavior. Exact official interior triangulation identity remains a separate exact-compatibility claim.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([
            sys.executable,
            "research/official_topology/m3/run_m3.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m18/run_m18.py",
        ]),
        run_step([
            sys.executable,
            "tools/validate_published_transition_topology.py",
        ]),
    ]
    m18 = read_json(M18_REPORT)
    topology = read_json(TOPOLOGY_REPORT)
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and m18.get("status")
        == "PASS_M18_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE"
        and topology.get("status")
        == "PASS_PUBLISHED_TRANSITION_TOPOLOGY_BEHAVIOR"
        and topology.get("published_transition_topology_behavior")
        == "PROVEN"
    )
    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m19.report.v1",
        "status": PASS_STATUS if base_ok else "FAIL_M19_TRANSITION_TOPOLOGY",
        "meaning": (
            "M19 proves published transition topology behavior for all 512 "
            "cases from public face-contour and D4/inversion rules plus "
            "clean-room minimal genus-zero fillings."
        ),
        "source_reference": topology.get("source_reference"),
        "published_transition_topology_behavior": (
            "PROVEN" if base_ok else "NOT_PROVEN"
        ),
        "official_triangle_triangulation_identity": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_vertex_encoding_equivalence": "NOT_PROVEN",
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "default_core_replaced": False,
        "m18_status": m18.get("status"),
        "topology_status": topology.get("status"),
        "metrics": topology.get("metrics", {}),
        "steps": steps,
        "outputs": {
            "topology_validation": str(
                TOPOLOGY_REPORT.relative_to(ROOT)
            ).replace("\\", "/"),
            "results": str(RESULTS.relative_to(ROOT)).replace("\\", "/"),
        },
        "claim_boundary": topology.get("claim_boundary", {}),
    }
    M19_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_step = run_step([
        sys.executable,
        "tools/m4_replacement_readiness.py",
    ])
    steps.append(readiness_step)
    readiness = read_json(READINESS)
    topology_gate = next(
        (
            gate
            for gate in readiness.get("gates", [])
            if gate.get("id") == "official_transition_topology_equivalence"
        ),
        {},
    )
    final_ok = (
        base_ok
        and readiness_step["returncode"] == 0
        and readiness.get("status")
        == "READY_M4_DEFAULT_TRANSITION_BACKEND_FUNCTIONAL_FULL_REPLACEMENT_BLOCKED"
        and topology_gate.get("status") == "PASS"
        and len(readiness.get("blocking_gate_ids", [])) == 6
        and readiness.get("next_milestone", {}).get("id")
        in {
            "M20_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE",
            "M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY",
        }
    )
    report["status"] = (
        PASS_STATUS if final_ok else "FAIL_M19_TRANSITION_TOPOLOGY"
    )
    report["steps"] = steps
    report["topology_gate_status"] = topology_gate.get("status")
    report["readiness_status"] = readiness.get("status")
    report["next_milestone"] = readiness.get("next_milestone", {})
    M19_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report, topology, readiness)
    print()
    print("M19:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
