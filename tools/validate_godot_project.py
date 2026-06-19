#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "godot"
STAGES = GODOT / "stages"

REQUIRED = [
    GODOT / "project.godot",
    STAGES / "01_runtime" / "DumpRuntimeData.gd",
    STAGES / "02_mesh_api" / "DumpMeshData.gd",
    STAGES / "03_seam_metrics" / "DumpSeamMetrics.gd",
    STAGES / "04_viewer" / "TransvoxelValidation.tscn",
    STAGES / "04_viewer" / "TransvoxelValidation.gd",
    STAGES / "04_viewer" / "HeadlessValidation.gd",
    STAGES / "06_interactive_sandbox" / "InteractiveSandbox.tscn",
    STAGES / "06_interactive_sandbox" / "InteractiveSandbox.gd",
    STAGES / "07_auto_interaction" / "DumpAutoInteraction.gd",
    GODOT / "generated" / "regular_tables.json",
    GODOT / "generated" / "transition_tables.json",
    GODOT / "generated" / "transvoxel_tables.json",
    GODOT / "generated" / "official_topology_candidate_tables.json",
    STAGES / "05_m4_candidate_metrics" / "DumpM4CandidateMetrics.gd",
    STAGES / "08_m4_candidate_viewer" / "DumpM4CandidateViewer.gd",
    STAGES / "09_m4_backend_compare" / "DumpM4BackendCompare.gd",
    STAGES / "10_m4_scripted_edit_compare" / "DumpM4ScriptedEditCompare.gd",
    STAGES / "11_m4_six_face_orientation" / "DumpM4SixFaceOrientation.gd",
    STAGES / "12_m4_corner_junctions" / "DumpM4CornerJunctions.gd",
]

EXPECTED_SCHEMAS = {
    "regular_tables.json": "boqsc.regular_tables.v1",
    "transition_tables.json": "boqsc.transition_tables.v1",
    "transvoxel_tables.json": "boqsc.transvoxel_tables.v1",
    "official_topology_candidate_tables.json": "boqsc.transvoxel.official_topology.m4.runtime_candidate.v1",
}


def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        print("godot preflight: FAIL")
        for p in missing:
            print("missing", p)
        return 1

    for name, schema in EXPECTED_SCHEMAS.items():
        path = GODOT / "generated" / name
        canonical = ROOT / "generated" / name
        data = json.loads(path.read_text(encoding="utf-8"))
        got = data.get("schema")
        if got != schema:
            print("godot preflight: FAIL")
            print(f"schema mismatch {name}: got {got!r}, expected {schema!r}")
            return 1
        if canonical.exists() and path.read_bytes() != canonical.read_bytes():
            print("godot preflight: FAIL")
            print(f"godot/generated/{name} is not byte-identical to generated/{name}; run tools/sync_godot_tables.py")
            return 1

    project = (GODOT / "project.godot").read_text(encoding="utf-8")
    if 'run/main_scene="res://stages/04_viewer/TransvoxelValidation.tscn"' not in project:
        print("godot preflight: FAIL")
        print("project.godot does not use the staged viewer scene")
        return 1

    scene = (STAGES / "04_viewer" / "TransvoxelValidation.tscn").read_text(encoding="utf-8")
    if "res://stages/04_viewer/TransvoxelValidation.gd" not in scene:
        print("godot preflight: FAIL")
        print("viewer scene does not reference staged validation script")
        return 1

    script = (STAGES / "04_viewer" / "TransvoxelValidation.gd").read_text(encoding="utf-8")
    needed_tokens = ["REGULAR_PATH", "TRANSITION_PATH", "_build_regular_chunk", "_build_transition_strip", "_count_open_edges"]
    for token in needed_tokens:
        if token not in script:
            print("godot preflight: FAIL")
            print("viewer script missing token", token)
            return 1

    interactive_scene = (STAGES / "06_interactive_sandbox" / "InteractiveSandbox.tscn").read_text(encoding="utf-8")
    if "res://stages/06_interactive_sandbox/InteractiveSandbox.gd" not in interactive_scene:
        print("godot preflight: FAIL")
        print("interactive scene does not reference staged sandbox script")
        return 1

    interactive_script = (STAGES / "06_interactive_sandbox" / "InteractiveSandbox.gd").read_text(encoding="utf-8")
    interactive_tokens = ["SESSION_PATH", "_add_edit", "_rebuild_world", "_write_session_report"]
    for token in interactive_tokens:
        if token not in interactive_script:
            print("godot preflight: FAIL")
            print("interactive script missing token", token)
            return 1

    auto_script = (STAGES / "07_auto_interaction" / "DumpAutoInteraction.gd").read_text(encoding="utf-8")
    auto_tokens = ["OUT_PATH", "_run_auto_interaction", "_strip_check", "_scripted_edits_for_field"]
    for token in auto_tokens:
        if token not in auto_script:
            print("godot preflight: FAIL")
            print("auto interaction script missing token", token)
            return 1

    m4_script = (STAGES / "05_m4_candidate_metrics" / "DumpM4CandidateMetrics.gd").read_text(encoding="utf-8")
    m4_tokens = ["M4_PATH", "OUT_PATH", "_validate_m4_candidate", "_validate_strips", "_validate_triangles"]
    for token in m4_tokens:
        if token not in m4_script:
            print("godot preflight: FAIL")
            print("M4 candidate script missing token", token)
            return 1

    m4_viewer_script = (STAGES / "08_m4_candidate_viewer" / "DumpM4CandidateViewer.gd").read_text(encoding="utf-8")
    m4_viewer_tokens = ["M4_PATH", "OUT_PATH", "_build_case_gallery", "_build_terrain_strip", "_make_array_mesh", "MeshDataTool"]
    for token in m4_viewer_tokens:
        if token not in m4_viewer_script:
            print("godot preflight: FAIL")
            print("M4 viewer script missing token", token)
            return 1

    m4_compare_script = (STAGES / "09_m4_backend_compare" / "DumpM4BackendCompare.gd").read_text(encoding="utf-8")
    m4_compare_tokens = ["DEFAULT_PATH", "M4_PATH", "OUT_PATH", "_build_backend", "_compare_backends", "_make_array_mesh", "MeshDataTool"]
    for token in m4_compare_tokens:
        if token not in m4_compare_script:
            print("godot preflight: FAIL")
            print("M4 backend compare script missing token", token)
            return 1

    m4_edit_compare_script = (STAGES / "10_m4_scripted_edit_compare" / "DumpM4ScriptedEditCompare.gd").read_text(encoding="utf-8")
    m4_edit_compare_tokens = ["DEFAULT_PATH", "M4_PATH", "OUT_PATH", "_scripted_edits_for_field", "_run_scenario", "_run_compare", "_make_array_mesh", "MeshDataTool"]
    for token in m4_edit_compare_tokens:
        if token not in m4_edit_compare_script:
            print("godot preflight: FAIL")
            print("M4 scripted edit compare script missing token", token)
            return 1

    m4_six_face_script = (STAGES / "11_m4_six_face_orientation" / "DumpM4SixFaceOrientation.gd").read_text(encoding="utf-8")
    m4_six_face_tokens = ["M4_PATH", "OUT_PATH", "_face_specs", "_frame_to_local", "_expected_transformed_cross", "_validate_face_cases", "_validate_face_seams", "ArrayMesh", "MeshDataTool"]
    for token in m4_six_face_tokens:
        if token not in m4_six_face_script:
            print("godot preflight: FAIL")
            print("M4 six-face orientation script missing token", token)
            return 1

    m4_corner_script = (STAGES / "12_m4_corner_junctions" / "DumpM4CornerJunctions.gd").read_text(encoding="utf-8")
    m4_corner_tokens = ["M4_PATH", "OUT_PATH", "_mapped_sample_positions", "_corner_frames", "_compare_shared_samples", "_compare_fingerprints", "_validate_cell", "ArrayMesh", "MeshDataTool"]
    for token in m4_corner_tokens:
        if token not in m4_corner_script:
            print("godot preflight: FAIL")
            print("M4 corner-junction script missing token", token)
            return 1

    for gd_path in sorted(STAGES.rglob("*.gd")):
        text = gd_path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":=" in stripped:
                print("godot preflight: FAIL")
                print(f"ambiguous := inference in {gd_path.relative_to(ROOT)}:{line_no}")
                return 1

    validation_dir = ROOT / "validation"
    validation_dir.mkdir(exist_ok=True)
    json_report = validation_dir / "godot_project_report.json"
    md_report = validation_dir / "godot_project_report.md"
    data = {
        "status": "PASS",
        "validated_files": [str(p.relative_to(ROOT)) for p in REQUIRED],
        "meaning": "Package preflight only. This does not execute Godot runtime scripts.",
        "layout": "staged_godot_validation_v1",
    }
    json_report.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Godot project preflight",
        "",
        "Status: PASS",
        "",
        "Validated files:",
    ]
    for item in REQUIRED:
        lines.append(f"- `{item.relative_to(ROOT)}`")
    lines.extend([
        "",
        "This preflight does not execute Godot. It verifies that the staged runtime validation project is packaged correctly.",
        "",
    ])
    md_report.write_text("\n".join(lines), encoding="utf-8")
    print("godot preflight: PASS")
    print(md_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
