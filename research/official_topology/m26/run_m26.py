#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run M26: pinned Godot Voxel integration and exact-candidate provenance audit."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
M26_DIR = ROOT / "research" / "official_topology" / "m26"
REPORT = M26_DIR / "m26_report.json"
RESULTS = M26_DIR / "results.md"
VALIDATION_JSON = ROOT / "validation" / "m26_exact_drop_in_report.json"
VALIDATION_MD = ROOT / "validation" / "m26_exact_drop_in_report.md"
INTEGRATION = M26_DIR / "m26_godot_voxel_integration.json"
PROVENANCE = M26_DIR / "m26_provenance_audit.json"
FULL_BUILD = M26_DIR / "m26_full_godot_voxel_build.json"
READINESS = ROOT / "validation" / "m4_replacement_readiness_report.json"
CLAIM_BOUNDARY = (
    ROOT / "validation" / "exact_compatibility_claim_boundary_report.json"
)
PROJECT_TRACKS = ROOT / "validation" / "project_tracks_report.json"
M25_LAYOUT = ROOT / "validation" / "m25_compatible_layout_report.json"
M25_CONSUMER = (
    ROOT
    / "research"
    / "official_topology"
    / "m25"
    / "m25_consumer_validation.json"
)
PASS_STATUS = "PASS_M26_EXACT_DROP_IN_INTEGRATION_PROVEN_PROVENANCE_BLOCKED"


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


def write_markdown(report: Dict[str, Any], path: Path) -> None:
    comparison = report["integration"]["comparison"]
    lines = [
        "# M26 Exact Drop-in Integration",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- Godot Voxel table API integration: "
        f"`{report['integration']['status']}`",
        f"- Regular cases: `{comparison['regular_case_matches']}/256`",
        f"- Transition cases: "
        f"`{comparison['transition_case_matches']}/512`",
        f"- Transition corner records: "
        f"`{comparison['transition_corner_matches']}/13`",
        f"- Mismatches: `{comparison['mismatch_count']}`",
        f"- Full Godot Voxel GDExtension build: "
        f"`{report['full_build']['status']}`",
        f"- Built DLL bytes: `{report['full_build']['dll_bytes']}`",
        f"- Exact semantic drop-in integration ready: "
        f"`{report['readiness']['exact_drop_in_integration_ready']}`",
        f"- Exact semantic drop-in 0BSD release ready: "
        f"`{report['readiness']['exact_drop_in_0bsd_replacement_ready']}`",
        f"- Drop-in release blockers: "
        f"`{', '.join(report['readiness']['drop_in_blocking_gate_ids'])}`",
        f"- Identity-only blockers: "
        f"`{', '.join(report['readiness']['identity_only_blocking_gate_ids'])}`",
        f"- Roadmap state: `{report['readiness']['next_milestone']['id']}`",
        "",
        "M26 proves exact semantic replacement through the pinned Godot Voxel "
        "table-source API and a full Zig GDExtension compile/link. The "
        "candidate remains research-only because M24 triangulation option "
        "indexes were calibrated by the MIT oracle.",
        "",
        "No zip artifact is built.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


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
        run_step([
            sys.executable,
            (
                "research/official_topology/m26/"
                "build_godot_voxel_replacement.py"
            ),
        ]),
        run_step([
            sys.executable,
            (
                "research/official_topology/m26/"
                "test_godot_voxel_integration.py"
            ),
        ]),
        run_step([
            sys.executable,
            (
                "research/official_topology/m26/"
                "test_full_godot_voxel_build.py"
            ),
        ]),
        run_step([
            sys.executable,
            "research/official_topology/m26/provenance_audit.py",
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
    integration = read_json(INTEGRATION)
    provenance = read_json(PROVENANCE)
    full_build = read_json(FULL_BUILD)
    readiness = read_json(READINESS)
    claim_boundary = read_json(CLAIM_BOUNDARY)
    project_tracks = read_json(PROJECT_TRACKS)
    m25_layout = read_json(M25_LAYOUT)
    m25_consumer = read_json(M25_CONSUMER)
    comparison = integration.get("comparison", {})
    dlls = [
        artifact
        for artifact in full_build.get("artifacts", [])
        if str(artifact.get("name", "")).lower().endswith(".dll")
    ]
    final_ok = (
        all(step["returncode"] == 0 for step in steps)
        and integration.get("status")
        == "PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION"
        and comparison.get("regular_case_matches") == 256
        and comparison.get("transition_case_matches") == 512
        and comparison.get("transition_corner_matches") == 13
        and comparison.get("mismatch_count") == 0
        and full_build.get("status")
        == "PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD"
        and len(dlls) == 1
        and int(dlls[0].get("bytes", 0)) > 0
        and provenance.get("status")
        == "PASS_M26_PROVENANCE_AUDIT_BLOCKED"
        and provenance.get("decision", {}).get(
            "exact_candidate_0bsd_provenance_cleared"
        )
        is False
        and readiness.get("status")
        in {
            (
                "READY_EXACT_DROP_IN_INTEGRATION_PROVEN_"
                "0BSD_PROVENANCE_BLOCKED"
            ),
            (
                "TERMINAL_EXACT_0BSD_TRANSVOXEL_CPP_"
                "REPLACEMENT_NOT_ACHIEVED"
            ),
        }
        and readiness.get("decisions", {}).get(
            "exact_drop_in_integration_ready"
        )
        is True
        and readiness.get("decisions", {}).get(
            "exact_drop_in_0bsd_replacement_ready"
        )
        is False
        and set(readiness.get("drop_in_blocking_gate_ids", []))
        == {"exact_0bsd_provenance_clearance"}
        and set(readiness.get("identity_only_blocking_gate_ids", []))
        == {
            "official_class_id_mapping",
            "official_regular_table_identity",
            "official_transvoxel_cpp_byte_identity",
        }
        and readiness.get("next_milestone", {}).get("id")
        in {
            "M27_INDEPENDENT_EXACT_TOPOLOGY_PROVENANCE",
            "NONE_TERMINAL",
        }
        and claim_boundary.get("status")
        == "PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY"
        and project_tracks.get("status") == "PASS"
        and m25_layout.get("status")
        == "PASS_M25_COMPATIBLE_TRANSVOXEL_CPP_LAYOUT"
        and m25_consumer.get("status")
        == "PASS_M25_UNCHANGED_STYLE_CPP_CONSUMER"
    )
    report = {
        "schema": "boqsc.transvoxel.official_topology.m26.report.v1",
        "status": PASS_STATUS if final_ok else "FAIL_M26_EXACT_DROP_IN",
        "meaning": (
            "M26 proves exact semantic replacement through the pinned Godot "
            "Voxel table API and a full Zig GDExtension build, then isolates "
            "0BSD provenance as the only semantic drop-in release blocker."
        ),
        "integration": {
            "status": integration.get("status"),
            "comparison": comparison,
            "godot_voxel": integration.get("godot_voxel", {}),
            "full_godot_module_build": integration.get(
                "full_godot_module_build", {}
            ),
        },
        "provenance": {
            "status": provenance.get("status"),
            "decision": provenance.get("decision", {}),
            "blocking_reason": provenance.get("blocking_reason"),
            "required_resolution": provenance.get("required_resolution"),
        },
        "full_build": {
            "status": full_build.get("status"),
            "compiler": full_build.get("compiler"),
            "dll_bytes": (
                int(dlls[0].get("bytes", 0)) if dlls else 0
            ),
            "artifacts": full_build.get("artifacts", []),
            "godot_cpp": full_build.get("godot_cpp", {}),
        },
        "readiness": {
            "status": readiness.get("status"),
            "exact_drop_in_integration_ready": readiness.get(
                "decisions", {}
            ).get("exact_drop_in_integration_ready"),
            "exact_drop_in_0bsd_replacement_ready": readiness.get(
                "decisions", {}
            ).get("exact_drop_in_0bsd_replacement_ready"),
            "drop_in_blocking_gate_ids": readiness.get(
                "drop_in_blocking_gate_ids", []
            ),
            "identity_only_blocking_gate_ids": readiness.get(
                "identity_only_blocking_gate_ids", []
            ),
            "next_milestone": readiness.get("next_milestone", {}),
        },
        "claim_boundary_status": claim_boundary.get("status"),
        "project_tracks_status": project_tracks.get("status"),
        "steps": steps,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    REPORT.write_text(encoded, encoding="utf-8")
    VALIDATION_JSON.write_text(encoded, encoding="utf-8")
    write_markdown(report, RESULTS)
    write_markdown(report, VALIDATION_MD)
    print()
    print("M26:", report["status"])
    print(RESULTS)
    return 0 if final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
