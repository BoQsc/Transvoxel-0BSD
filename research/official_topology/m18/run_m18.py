#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M18: published reference-convention equivalence proof."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M18_DIR = ROOT / "research" / "official_topology" / "m18"
SPEC = ROOT / "validation" / "official_reference_convention_research.json"
MATRIX = ROOT / "validation" / "reference_convention_matrix.json"
VALIDATION = ROOT / "validation" / "reference_convention_report.json"
C_REPORT = M18_DIR / "m18_c_validation.json"
STRICT_REPORT = ROOT / "validation" / "strict_correctness_audit.json"
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
M18_REPORT = M18_DIR / "m18_report.json"
RESULTS = M18_DIR / "results.md"
PASS_STATUS = "PASS_M18_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE"


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
    validation: Dict[str, Any],
    readiness: Dict[str, Any],
) -> None:
    metrics = validation.get("metrics", {})
    winding = metrics.get("winding", {})
    lines = [
        "# M18 Published Reference-Convention Validation",
        "",
        "M18 proves M4's published sample/sign/case-index/face/winding convention through an explicit no-copy bijection.",
        "",
        f"- Status: `{report['status']}`",
        f"- Python convention proof: `{validation.get('status')}`",
        f"- Zig C API proof: `{report.get('c_status')}`",
        f"- Readiness reference gate: `{report.get('reference_gate_status')}`",
        "",
        "## Exhaustive coverage",
        "",
        f"- Case mappings: `{metrics.get('case_mapping_cases')}`",
        f"- Distinct published indexes: `{metrics.get('distinct_reference_indexes')}`",
        f"- D4 mapping comparisons: `{metrics.get('d4_mapping_comparisons')}`",
        f"- Six-face frames: `{metrics.get('face_frames')}`",
        f"- Wound triangles: `{winding.get('triangles')}`",
        f"- Coherent components: `{winding.get('components')}`",
        f"- Same-topology complement pairs: `{winding.get('complement_pairs_same_topology')}`",
        f"- Reverse-wound complement pairs: `{winding.get('complement_pairs_reverse_wound')}`",
        "",
        "## Readiness effect",
        "",
        f"- Remaining blocking gates: `{len(readiness.get('blocking_gate_ids', []))}`",
        f"- Next milestone: `{readiness.get('next_milestone', {}).get('id')}`",
        "",
        "M18 proves the published algorithmic reference convention. Official transition triangulation topology, class IDs, vertex encoding, regular-cell equivalence, consumer compatibility, and table bytes remain separate.",
        "",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    steps = [
        run_step([
            sys.executable,
            "research/official_topology/m4/run_m4.py",
        ]),
        run_step([sys.executable, "tools/sync_godot_tables.py"]),
        run_step([
            sys.executable,
            "research/official_topology/derive_reference_convention.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/reference_convention_matrix.py",
        ]),
        run_step([
            sys.executable,
            "tools/validate_reference_convention.py",
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m18/test_reference_convention_c.py",
        ]),
        run_step([sys.executable, "tools/strict_correctness_audit.py"]),
    ]
    spec = read_json(SPEC)
    matrix = read_json(MATRIX)
    validation = read_json(VALIDATION)
    c_report = read_json(C_REPORT)
    strict = read_json(STRICT_REPORT)
    base_ok = (
        all(step["returncode"] == 0 for step in steps)
        and spec.get("official_convention_status") == "PROVEN"
        and matrix.get("official_reference_equivalence") == "PROVEN"
        and validation.get("status")
        == "PASS_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE"
        and validation.get("reference_equivalence_status") == "PROVEN"
        and c_report.get("status")
        == "PASS_M18_ZIG_PUBLISHED_REFERENCE_CONVENTION_API"
        and strict.get("matrix", {}).get(
            "same_orientation_sign_convention_as_reference"
        )
        == "PROVEN"
    )

    report: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.official_topology.m18.report.v1",
        "status": PASS_STATUS if base_ok else "FAIL_M18_REFERENCE_CONVENTION",
        "meaning": (
            "M18 proves the M4 candidate's equivalence to the published "
            "algorithmic transition-cell convention through an explicit "
            "bijection between local and Figure 4.17 case indexes."
        ),
        "source_reference": spec.get("source"),
        "official_reference_convention_equivalence": (
            "PROVEN" if base_ok else "NOT_PROVEN"
        ),
        "official_transition_topology_equivalence": "NOT_PROVEN",
        "official_class_id_mapping": "NOT_PROVEN",
        "official_vertex_encoding_equivalence": "NOT_PROVEN",
        "official_transvoxel_cpp_byte_identity": "NOT_PROVEN",
        "default_core_replaced": False,
        "spec_status": spec.get("status"),
        "matrix_status": matrix.get("status"),
        "validation_status": validation.get("status"),
        "c_status": c_report.get("status"),
        "strict_audit_status": strict.get("status"),
        "metrics": validation.get("metrics", {}),
        "steps": steps,
        "outputs": {
            "source_spec": str(SPEC.relative_to(ROOT)).replace("\\", "/"),
            "frame_matrix": str(MATRIX.relative_to(ROOT)).replace("\\", "/"),
            "validation": str(VALIDATION.relative_to(ROOT)).replace("\\", "/"),
            "c_validation": str(C_REPORT.relative_to(ROOT)).replace("\\", "/"),
            "results": str(RESULTS.relative_to(ROOT)).replace("\\", "/"),
        },
        "claim_boundary": validation.get("claim_boundary", {}),
    }
    M18_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readiness_step = run_step([
        sys.executable,
        "tools/m4_replacement_readiness.py",
    ])
    steps.append(readiness_step)
    readiness = read_json(READINESS)
    reference_gate = next(
        (
            gate
            for gate in readiness.get("gates", [])
            if gate.get("id") == "official_reference_convention_equivalence"
        ),
        {},
    )
    final_ok = (
        base_ok
        and readiness_step["returncode"] == 0
        and readiness.get("status")
        == "READY_M4_DEFAULT_TRANSITION_BACKEND_FUNCTIONAL_FULL_REPLACEMENT_BLOCKED"
        and reference_gate.get("status") == "PASS"
        and len(readiness.get("blocking_gate_ids", [])) == 6
        and readiness.get("next_milestone", {}).get("id")
        in {
            "M19_OFFICIAL_TRANSITION_TOPOLOGY_VALIDATION",
            "M20_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE",
            "M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY",
        }
    )
    report["status"] = (
        PASS_STATUS if final_ok else "FAIL_M18_REFERENCE_CONVENTION"
    )
    report["steps"] = steps
    report["reference_gate_status"] = reference_gate.get("status")
    report["readiness_status"] = readiness.get("status")
    report["next_milestone"] = readiness.get("next_milestone", {})
    M18_REPORT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_results(report, validation, readiness)
    print()
    print("M18:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
