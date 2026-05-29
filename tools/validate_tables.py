#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate every clean-room table generator in this repository."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Dict, List


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_module(filename: str, name: str):
    path = root_dir() / "tools" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load " + filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def table_stats(table: Dict[str, object]) -> Dict[str, object]:
    cases = table.get("cases", [])
    vertex_counts = [len(c["vertices"]) for c in cases]
    triangle_counts = [len(c["triangles"]) for c in cases]
    return {
        "schema": table.get("schema"),
        "status": table.get("status"),
        "sha256_without_this_field": table.get("sha256_without_this_field"),
        "case_count": len(cases),
        "non_empty_cases": sum(1 for c in cases if c["triangles"]),
        "empty_cases": sum(1 for c in cases if not c["triangles"]),
        "min_vertices_per_case": min(vertex_counts) if vertex_counts else None,
        "max_vertices_per_case": max(vertex_counts) if vertex_counts else None,
        "min_triangles_per_case": min(triangle_counts) if triangle_counts else None,
        "max_triangles_per_case": max(triangle_counts) if triangle_counts else None,
        "total_vertices_across_cases": sum(vertex_counts),
        "total_triangles_across_cases": sum(triangle_counts),
    }


def write_markdown(report: Dict[str, object], path: Path) -> None:
    lines: List[str] = []
    lines.append("# All Table Validation Report")
    lines.append("")
    lines.append("This validates only the clean-room generators in this repository. It does not compare against or copy Eric Lengyel's MIT-licensed Transvoxel.cpp table values.")
    lines.append("")
    lines.append(f"Overall OK: `{report['ok']}`")
    lines.append("")
    for name, item in report["tables"].items():
        lines.append(f"## {name}")
        lines.append("")
        stats = item["stats"]
        lines.append(f"- OK: `{item['ok']}`")
        lines.append(f"- Schema: `{stats['schema']}`")
        lines.append(f"- Status: `{stats['status']}`")
        lines.append(f"- SHA-256: `{stats['sha256_without_this_field']}`")
        lines.append(f"- Cases: `{stats['case_count']}`")
        lines.append(f"- Non-empty cases: `{stats['non_empty_cases']}`")
        lines.append(f"- Empty cases: `{stats['empty_cases']}`")
        lines.append(f"- Vertices per case: `{stats['min_vertices_per_case']}` .. `{stats['max_vertices_per_case']}`")
        lines.append(f"- Triangles per case: `{stats['min_triangles_per_case']}` .. `{stats['max_triangles_per_case']}`")
        lines.append(f"- Total vertex-pairs across cases: `{stats['total_vertices_across_cases']}`")
        lines.append(f"- Total triangles across cases: `{stats['total_triangles_across_cases']}`")
        if item["errors"]:
            lines.append("")
            lines.append("Errors:")
            for err in item["errors"]:
                lines.append(f"- {err}")
        lines.append("")
    lines.append("## Meaning")
    lines.append("")
    lines.append("These checks prove deterministic generation and structural sanity for the local 0BSD tables. They do not prove that the tables are equivalent to official Transvoxel lookup tables or production-ready for every terrain edit.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    regular = load_module("generate_regular.py", "regular")
    transition = load_module("generate_transition.py", "transition")

    items = {}
    for name, module in [("regular", regular), ("transition", transition)]:
        table = module.generate_tables()
        errors = module.verify_table(table)
        items[name] = {
            "ok": not errors,
            "errors": errors,
            "stats": table_stats(table),
        }

    report = {
        "ok": all(item["ok"] for item in items.values()),
        "tables": items,
    }
    out_dir = root_dir() / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "all_tables_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, out_dir / "all_tables_report.md")
    print("all tables report:", out_dir / "all_tables_report.md")
    print("ok:", report["ok"])
    for name, item in items.items():
        print(name, "sha256:", item["stats"]["sha256_without_this_field"])
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
