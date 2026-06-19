#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Run the full clean-room proof suite in-process with visible progress."""
from __future__ import annotations

import json
import os
import runpy
import sys
import time
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"

STEPS: list[list[str]] = [
    ["tools/generate_regular.py", "--out", "generated"],
    ["tools/generate_transition.py", "--out", "generated"],
    ["tools/export_transvoxel.py"],
    ["tools/sync_godot_tables.py"],
    ["tools/verify_generated_tables.py"],
    ["tools/validate_tables.py"],
    ["tools/validate_transition.py"],
    ["tools/validate_transvoxel.py"],
    ["tools/validate_boundaries.py"],
    ["tools/validate_neighbors.py"],
    ["tools/validate_chunks.py"],
    ["tools/validate_godot_project.py"],
    ["tools/validate_m4_godot_candidate.py"],
    ["tools/validate_m4_godot_viewer.py"],
    ["tools/validate_m4_godot_backend_compare.py"],
    ["tools/validate_m4_godot_scripted_edit_compare.py"],
    ["tools/validate_m4_six_face_orientation.py"],
    ["tools/validate_m4_corner_junctions.py"],
    ["tools/dump_proof_data.py"],
    ["tools/external_alignment_report.py"],
    ["tools/topology_signature_analysis.py"],
    ["tools/official_equivalence_research.py"],
    ["tools/topology_comparison_no_copy.py"],
    ["research/official_topology/derive_transition_classes.py"],
    ["research/official_topology/derive_reference_convention.py"],
    ["research/official_topology/derive_candidate_73_classes.py"],
    ["research/official_topology/reference_convention_matrix.py"],
    ["tools/validate_reference_convention.py"],
    ["tools/validate_published_transition_topology.py"],
    ["research/official_topology/official_topology_constraints.py"],
    ["tools/strict_correctness_audit.py"],
    ["tools/m4_replacement_readiness.py"],
    ["tools/project_tracks_report.py"],
    ["tools/build_dist.py"],
    ["tools/release_candidate_report.py"],
    ["tools/github_ready_report.py"],
]

PROVES = [
    "The regular and transition tables regenerate deterministically.",
    "The exported transvoxel_tables ABI round-trips to the canonical JSON.",
    "The generated C header is readable by a C compiler when one is available.",
    "All 512 transition cases expose the expected boundary contour from the documented transition-cell boundary triangulation.",
    "Side-face contour fingerprints are deterministic and match on opposite side faces.",
    "Deterministic chunk strips from several sign fields have matching shared side-face fingerprints.",
    "The Godot validation project is packaged with the expected scene, scripts, and generated JSON tables copied from the canonical generated outputs.",
    "The M4 candidate table is synced into the Godot generated-data path and passes Godot-style non-visual seam metrics without executing Godot.",
    "The M4 candidate Godot viewer/export stage is packaged and statically validated; when a Godot output exists, that output is also validated.",
    "The default-vs-M4 Godot backend comparison stage is packaged and statically validated; when a Godot output exists, that output is also validated.",
    "The default-vs-M4 Godot scripted-edit comparison stage is packaged and statically validated; when a Godot output exists, that output is also validated.",
    "The M4 six-face orientation stage is packaged and statically validated; committed M15 evidence records exhaustive Zig C and actual Godot runtime coverage across all six right-handed face frames.",
    "The M4 mapped corner-junction stage is packaged and statically validated; committed M16 evidence records coherent winding and three-face junction closure across all eight signed corner octants.",
    "Committed M17 evidence records a passing M4-selected production gate and separates default-transition-backend readiness from functional full replacement.",
    "Committed M18 evidence proves the published transition sample/sign/case-index/face/winding convention through an exhaustive no-copy bijection and Zig C API test.",
    "Committed M19 evidence proves published transition face contours, D4/inversion behavior classes, and minimal genus-zero fillings for all 512 cases.",
    "An M4 replacement-readiness gate separates optional-backend readiness, default-backend readiness, functional full replacement, and exact table compatibility.",
    "A non-visual proof data dump is written to proof/proof_dump.json and proof/tables/*.csv before visual validation is trusted.",
    "Failure OBJ export is available as a separate diagnostic command: python tools/export_failure_obj.py.",
    "An external-alignment report checks the generated project against published Transvoxel-style outcome requirements.",
    "A topology-signature analysis groups all 512 generated transition cases by generated topology without reading external table values.",
    "An official-equivalence research report documents the no-copy boundary, 73-class status, naive symmetry orbit counts, and topology-signature status.",
    "A topology-comparison report compares public structural expectations without reading external table values.",
    "A strict correctness audit checks duplicates, degenerates, complement winding, midpoint self-intersections, 73-class status, reference convention status, and corner-junction evidence.",
    "A project-tracks report freezes the working independent core separately from the official-topology research track.",
    "Track B research now runs a no-copy candidate 73-class derivation search, a proven published reference-convention matrix, and public structural constraint checks.",
    "A release-candidate report verifies the small public core zip contains expected files and no proof/Godot/research clutter.",
    "A GitHub-ready report verifies release text, issue templates, CI workflow, and repository publishing files are present.",
]

DOES_NOT_PROVE = [
    "It does not prove byte-for-byte compatibility with Eric Lengyel's MIT-licensed Transvoxel.cpp tables.",
    "It does not prove the table has the official 73-equivalence-class compression.",
    "It does not prove the Godot scene was executed unless you also run Godot locally.",
    "It does not prove the M4 Godot stage was executed unless you also run that Godot stage locally.",
    "It does not prove the M4 Godot viewer/export stage was executed unless you run RUN_M11.cmd or that Godot stage locally.",
    "It does not prove the M4/default Godot backend comparison stage was executed unless you run RUN_M12.cmd or that Godot stage locally.",
    "It does not prove the M4/default Godot scripted-edit comparison stage was executed unless you run RUN_M13.cmd or that Godot stage locally.",
    "It does not regenerate the committed M15 Godot runtime evidence unless you run RUN_M15.cmd; source-only proof keeps that distinction explicit.",
    "It does not regenerate the committed M16 Godot runtime evidence unless you run RUN_M16.cmd.",
    "It does not rerun the M4-selected production gate unless you run RUN_M17.cmd.",
    "It does not rerun the Zig C portion of the published reference-convention gate unless you run RUN_M18.cmd.",
    "It does not make M4 the default backend while the replacement-readiness report contains blocking gates.",
    "It does not replace the final production terrain/chunk/GDExtension integration.",
    "It does not pass the production gate until Godot runtime dumps and real seam_metrics.json exist.",
    "It does not prove exact visual/artistic terrain quality in a finished game world.",
    "It proves the published reference convention and transition topology behavior but still marks official class numbers, exact interior triangulation identity, vertex encoding, and bytes as NOT_PROVEN.",
    "It does not claim exhaustive proof for every possible production corner or multi-neighbor streaming junction.",
    "It keeps official-topology research separate and explicitly IN_PROGRESS / NOT_PROVEN.",
    "It does not treat the 70-class C4+complement observation or any candidate orbit split as official 73-class proof.",
]


def run_step(args: List[str]) -> Dict[str, object]:
    label = " ".join(args)
    print("RUN", label, flush=True)
    old_argv = sys.argv[:]
    old_cwd = Path.cwd()
    start = time.monotonic()
    ok = False
    code: object = 0
    try:
        os.chdir(ROOT)
        sys.argv = [str(ROOT / args[0]), *args[1:]]
        try:
            runpy.run_path(str(ROOT / args[0]), run_name="__main__")
            code = 0
            ok = True
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 0
            ok = code == 0
    except BaseException as exc:
        code = type(exc).__name__
        ok = False
        print("ERROR", label, repr(exc), flush=True)
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
    elapsed = time.monotonic() - start
    print(("PASS" if ok else "FAIL"), label, f"{elapsed:.2f}s", flush=True)
    return {"command": label, "ok": ok, "returncode": code, "elapsed_seconds": round(elapsed, 3)}


def write_markdown(report: Dict[str, object]) -> None:
    lines = [
        "# Proof Suite Report",
        "",
        f"Overall: **{'PASS' if report['ok'] else 'FAIL'}**",
        "",
        "This proof suite validates the generated 0BSD tables against their own documented table contract. It does not claim byte-for-byte identity with any external table file.",
        "",
        "## Steps",
        "",
    ]
    for step in report["steps"]:
        lines.append(f"- `{'PASS' if step['ok'] else 'FAIL'}` — `{step['command']}` — {step['elapsed_seconds']}s")
    lines.extend(["", "## What this proves", "", *[f"- {x}" for x in PROVES], ""])
    lines.extend(["## What this does not prove", "", *[f"- {x}" for x in DOES_NOT_PROVE], ""])
    VALIDATION.mkdir(exist_ok=True)
    (VALIDATION / "proof_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    VALIDATION.mkdir(exist_ok=True)
    steps = [run_step(step) for step in STEPS]
    ok = all(bool(step["ok"]) for step in steps)
    report: Dict[str, object] = {"ok": ok, "steps": steps, "proves": PROVES, "does_not_prove": DOES_NOT_PROVE}
    (VALIDATION / "proof_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print("proof suite:", "PASS" if ok else "FAIL", flush=True)
    print(VALIDATION / "proof_report.md", flush=True)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
