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
    ["tools/dump_proof_data.py"],
    ["tools/external_alignment_report.py"],
    ["tools/topology_signature_analysis.py"],
    ["tools/official_equivalence_research.py"],
    ["tools/topology_comparison_no_copy.py"],
    ["research/official_topology/derive_transition_classes.py"],
    ["research/official_topology/derive_reference_convention.py"],
    ["research/official_topology/derive_candidate_73_classes.py"],
    ["research/official_topology/reference_convention_matrix.py"],
    ["research/official_topology/official_topology_constraints.py"],
    ["tools/strict_correctness_audit.py"],
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
    "A non-visual proof data dump is written to proof/proof_dump.json and proof/tables/*.csv before visual validation is trusted.",
    "Failure OBJ export is available as a separate diagnostic command: python tools/export_failure_obj.py.",
    "An external-alignment report checks the generated project against published Transvoxel-style outcome requirements.",
    "A topology-signature analysis groups all 512 generated transition cases by generated topology without reading external table values.",
    "An official-equivalence research report documents the no-copy boundary, 73-class status, naive symmetry orbit counts, and topology-signature status.",
    "A topology-comparison report compares public structural expectations without reading external table values.",
    "A strict correctness audit checks duplicates, degenerates, complement winding, midpoint self-intersections, 73-class status, reference convention status, and corner-junction evidence.",
    "A project-tracks report freezes the working independent core separately from the official-topology research track.",
    "Track B research now runs a no-copy candidate 73-class derivation search, an internal reference convention matrix, and public structural constraint checks.",
    "A release-candidate report verifies the small public core zip contains expected files and no proof/Godot/research clutter.",
    "A GitHub-ready report verifies release text, issue templates, CI workflow, and repository publishing files are present.",
]

DOES_NOT_PROVE = [
    "It does not prove byte-for-byte compatibility with Eric Lengyel's MIT-licensed Transvoxel.cpp tables.",
    "It does not prove the table has the official 73-equivalence-class compression.",
    "It does not prove the Godot scene was executed unless you also run Godot locally.",
    "It does not replace the final production terrain/chunk/GDExtension integration.",
    "It does not pass the production gate until Godot runtime dumps and real seam_metrics.json exist.",
    "It does not prove exact visual/artistic terrain quality in a finished game world.",
    "It still marks official 73-class equivalence, exact reference sign/orientation convention equivalence, and original topology equivalence as NOT_PROVEN.",
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
