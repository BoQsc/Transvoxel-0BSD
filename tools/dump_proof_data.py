#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Dump non-visual proof data for production validation.

This tool writes a machine-readable data dump that can be reviewed without
opening Godot or Blender. It is intentionally verbose. The point is to make the
state of the generated tables and current proof gates inspectable before any
visual validation is trusted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_boundaries import expected_segments_by_face, actual_boundary_segments  # type: ignore  # noqa: E402


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def triangle_count(table: Dict[str, Any]) -> int:
    return sum(len(case.get("triangles", [])) for case in table.get("cases", []))


def vertex_count(table: Dict[str, Any]) -> int:
    return sum(len(case.get("vertices", [])) for case in table.get("cases", []))


def histogram(values: Iterable[int]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        key = str(v)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))


def dump_case_metrics(table: Dict[str, Any], out_csv: Path, out_json: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in table.get("cases", []):
        rows.append({
            "case": int(case.get("case", -1)),
            "inside_count": len(case.get("inside_samples", [])),
            "vertex_count": len(case.get("vertices", [])),
            "triangle_count": len(case.get("triangles", [])),
            "boundary_edge_count": len(actual_boundary_segments(case)) if "boundary_triangles" in table else "",
        })
    out_json.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["case"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def dump_transition_faces(table: Dict[str, Any], out_csv: Path, out_json: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in table.get("cases", []):
        idx = int(case.get("case", -1))
        by_face = expected_segments_by_face(table, idx)
        row: Dict[str, Any] = {"case": idx}
        for name, segs in by_face.items():
            row[f"{name}_segments"] = len(segs)
        row["total_segments"] = sum(len(segs) for segs in by_face.values())
        rows.append(row)
    out_json.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    fields = list(rows[0].keys()) if rows else ["case"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def collect_validation_reports() -> Dict[str, Any]:
    names = [
        "validation_report.json",
        "all_tables_report.json",
        "transvoxel_report.json",
        "boundary_report.json",
        "neighbor_report.json",
        "chunk_report.json",
        "godot_project_report.json",
        "proof_report.json",
    ]
    reports: Dict[str, Any] = {}
    for name in names:
        path = ROOT / "validation" / name
        if path.exists():
            try:
                reports[name] = load_json(path)
            except Exception as exc:
                reports[name] = {"read_error": repr(exc)}
        else:
            reports[name] = {"missing": True}
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="proof")
    args = parser.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    tables_out = out / "tables"
    tables_out.mkdir(exist_ok=True)

    regular_path = ROOT / "generated" / "regular_tables.json"
    transition_path = ROOT / "generated" / "transition_tables.json"
    transvoxel_path = ROOT / "generated" / "transvoxel_tables.json"
    regular = load_json(regular_path)
    transition = load_json(transition_path)
    transvoxel = load_json(transvoxel_path)

    regular_rows = dump_case_metrics(regular, tables_out / "regular_case_metrics.csv", tables_out / "regular_case_metrics.json")
    transition_rows = dump_case_metrics(transition, tables_out / "transition_case_metrics.csv", tables_out / "transition_case_metrics.json")
    face_rows = dump_transition_faces(transition, tables_out / "transition_face_segments.csv", tables_out / "transition_face_segments.json")

    summary: Dict[str, Any] = {
        "schema": "boqsc.transvoxel.production_proof_dump.v1",
        "status": "DATA_DUMP_ONLY_NOT_PRODUCTION_PASS",
        "purpose": "Non-visual data dump used before visual validation or production claims.",
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
        },
        "files": {
            "generated/regular_tables.json": {"sha256": sha256_file(regular_path), "bytes": regular_path.stat().st_size},
            "generated/transition_tables.json": {"sha256": sha256_file(transition_path), "bytes": transition_path.stat().st_size},
            "generated/transvoxel_tables.json": {"sha256": sha256_file(transvoxel_path), "bytes": transvoxel_path.stat().st_size},
        },
        "regular": {
            "schema": regular.get("schema"),
            "case_count": len(regular.get("cases", [])),
            "total_vertices": vertex_count(regular),
            "total_triangles": triangle_count(regular),
            "triangles_per_case_histogram": histogram(int(r["triangle_count"]) for r in regular_rows),
            "vertices_per_case_histogram": histogram(int(r["vertex_count"]) for r in regular_rows),
        },
        "transition": {
            "schema": transition.get("schema"),
            "status": transition.get("status"),
            "warning": transition.get("warning"),
            "case_count": len(transition.get("cases", [])),
            "total_vertices": vertex_count(transition),
            "total_triangles": triangle_count(transition),
            "boundary_triangle_count": len(transition.get("boundary_triangles", [])),
            "tetrahedron_count": len(transition.get("tetrahedra", [])),
            "sample_count": len(transition.get("sample_positions", [])),
            "triangles_per_case_histogram": histogram(int(r["triangle_count"]) for r in transition_rows),
            "vertices_per_case_histogram": histogram(int(r["vertex_count"]) for r in transition_rows),
            "boundary_segments_per_case_histogram": histogram(int(r["total_segments"]) for r in face_rows),
        },
        "transvoxel_export": {
            "schema": transvoxel.get("schema"),
            "status": transvoxel.get("status"),
            "compression": transvoxel.get("compression"),
            "sha256": transvoxel.get("sha256"),
            "table_contract": transvoxel.get("table_contract"),
        },
        "validation_reports": collect_validation_reports(),
        "next_required_data": [
            "godot/runtime_dump.json from res://scripts/DumpRuntimeData.gd",
            "godot/mesh_api_dump.json from res://scripts/DumpMeshData.gd",
            "real LOD0-transition-LOD1 seam_metrics.json with seam_open_edges only, not total outer edges",
            "all six chunk-face directions with multiple SDF fields and live edit regeneration",
        ],
    }

    (out / "proof_dump.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Production Proof Data Dump",
        "",
        "Status: **DATA_DUMP_ONLY_NOT_PRODUCTION_PASS**",
        "",
        "This file is intentionally not a visual validation report. It records the table and proof data that must be inspected before trusting any rendered screenshot.",
        "",
        "## Table summary",
        "",
        f"- Regular cases: {summary['regular']['case_count']}",
        f"- Regular triangles: {summary['regular']['total_triangles']}",
        f"- Transition cases: {summary['transition']['case_count']}",
        f"- Transition triangles: {summary['transition']['total_triangles']}",
        f"- Transition boundary triangles: {summary['transition']['boundary_triangle_count']}",
        f"- Transvoxel export schema: `{summary['transvoxel_export']['schema']}`",
        "",
        "## Required next data before production proof",
        "",
    ]
    lines.extend(f"- {x}" for x in summary["next_required_data"])
    lines.extend(["", "## Generated files", "", "- `proof/proof_dump.json`", "- `proof/tables/regular_case_metrics.csv`", "- `proof/tables/transition_case_metrics.csv`", "- `proof/tables/transition_face_segments.csv`", ""])
    (out / "proof_dump.md").write_text("\n".join(lines), encoding="utf-8")
    print("proof data dump: wrote", out / "proof_dump.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
