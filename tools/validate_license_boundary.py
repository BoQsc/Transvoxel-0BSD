#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Enforce the 0BSD public-core / MIT exact-data license boundary."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "official_topology" / "MIT_ARTIFACTS.json"
REPORT_JSON = ROOT / "validation" / "license_boundary_report.json"
REPORT_MD = ROOT / "validation" / "license_boundary_report.md"

EXPECTED_MIT_ARTIFACTS = {
    "research/official_topology/m24/topology_rules.json",
    "research/official_topology/m24/generated/m24_exact_topology_tables.json",
    "research/official_topology/m24/generated/m24_exact_topology_tables.h",
    "research/official_topology/m25/generated/m25_compatible_layout.json",
    "research/official_topology/m25/generated/Transvoxel.cpp",
    "research/official_topology/m26/generated/transvoxel_tables.cpp",
}

MIT_JSON_ARTIFACTS = {
    path for path in EXPECTED_MIT_ARTIFACTS if path.endswith(".json")
}
MIT_TEXT_ARTIFACTS = EXPECTED_MIT_ARTIFACTS - MIT_JSON_ARTIFACTS

AGGREGATE_REPORTS = {
    "validation/official_oracle_comparison_report.json",
    "research/official_topology/m23/m23_report.json",
    "validation/m24_exact_topology_report.json",
    "research/official_topology/m24/m24_report.json",
    "validation/m25_compatible_layout_report.json",
    "research/official_topology/m25/m25_report.json",
    "research/official_topology/m26/generated/godot_voxel_replacement_layout.json",
    "research/official_topology/m26/m26_godot_voxel_integration.json",
    "research/official_topology/m26/m26_full_godot_voxel_build.json",
    "research/official_topology/m26/m26_provenance_audit.json",
    "research/official_topology/m26/m26_report.json",
    "validation/m26_exact_drop_in_report.json",
    "research/official_topology/m27/m27_terminal_audit.json",
    "research/official_topology/m27/m27_report.json",
    "validation/m27_terminal_roadmap_report.json",
}

FORBIDDEN_AGGREGATE_KEYS = {
    "cases",
    "option_indexes",
    "annulus_signature",
    "case_class",
    "class_data",
    "vertex_data",
    "vertex_refs",
    "triangles",
    "corner_data",
}

PUBLIC_0BSD_ROOTS = (
    ROOT / "include",
    ROOT / "src",
    ROOT / "generated",
    ROOT / "core" / "independent",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def exact_key_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_AGGREGATE_KEYS:
                hits.append(child_path)
            hits.extend(exact_key_hits(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(exact_key_hits(child, f"{path}[{index}]"))
    return hits


def assignment_list(path: Path, name: str) -> list[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                value = ast.literal_eval(node.value)
                if isinstance(value, list) and all(isinstance(item, str) for item in value):
                    return value
    raise ValueError(f"{name} string list not found in {rel(path)}")


def iter_public_files() -> Iterable[Path]:
    for root in PUBLIC_0BSD_ROOTS:
        for path in root.rglob("*"):
            if path.is_file():
                yield path


def write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# License Boundary Validation",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- MIT exact artifacts: `{report['metrics']['mit_artifact_count']}`",
        f"- Aggregate-only reports: `{report['metrics']['aggregate_report_count']}`",
        f"- Public 0BSD files scanned: `{report['metrics']['public_0bsd_files_scanned']}`",
        f"- MIT artifacts in public distribution list: `{report['metrics']['mit_artifacts_in_dist']}`",
        "",
    ]
    if report["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_artifacts = set(manifest.get("artifacts", []))
    if manifest_artifacts != EXPECTED_MIT_ARTIFACTS:
        errors.append(
            "MIT artifact manifest mismatch: expected "
            f"{sorted(EXPECTED_MIT_ARTIFACTS)}, got {sorted(manifest_artifacts)}"
        )
    if manifest.get("artifacts_license") != "MIT":
        errors.append("MIT artifact manifest does not declare MIT")
    if manifest.get("license_file") != "LICENSES/MIT.txt":
        errors.append("MIT artifact manifest has the wrong license file")

    for rel_path in sorted(MIT_JSON_ARTIFACTS):
        path = ROOT / rel_path
        if not path.is_file():
            errors.append("missing MIT JSON artifact: " + rel_path)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("license") != "MIT":
            errors.append(rel_path + ": missing license=MIT")
        if data.get("license_file") != "LICENSES/MIT.txt":
            errors.append(rel_path + ": wrong MIT license file")
        if data.get("copyright") != "Copyright (c) 2009 Eric Lengyel":
            errors.append(rel_path + ": missing MIT copyright attribution")

    for rel_path in sorted(MIT_TEXT_ARTIFACTS):
        path = ROOT / rel_path
        if not path.is_file():
            errors.append("missing MIT text artifact: " + rel_path)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")[:8192]
        if "SPDX-License-Identifier: MIT" not in text:
            errors.append(rel_path + ": missing MIT SPDX identifier")
        if "Copyright (c) 2009 Eric Lengyel" not in text:
            errors.append(rel_path + ": missing MIT copyright attribution")
        if "LICENSES/MIT.txt" not in text:
            errors.append(rel_path + ": missing MIT license-file reference")

    for rel_path in sorted(AGGREGATE_REPORTS):
        path = ROOT / rel_path
        if not path.is_file():
            errors.append("missing aggregate report: " + rel_path)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        hits = exact_key_hits(data)
        if hits:
            errors.append(
                rel_path + ": exact selection/array keys in 0BSD report: "
                + ", ".join(hits[:12])
            )

    public_files = list(iter_public_files())
    for path in public_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "SPDX-License-Identifier: MIT" in text:
            errors.append(rel(path) + ": MIT SPDX marker inside public 0BSD tree")

    core_files = set(
        assignment_list(ROOT / "tools" / "build_dist.py", "CORE_FILES")
    )
    mit_in_dist = sorted(core_files & EXPECTED_MIT_ARTIFACTS)
    if mit_in_dist:
        errors.append("MIT exact artifacts present in CORE_FILES: " + str(mit_in_dist))
    research_in_dist = sorted(
        path for path in core_files if path.startswith("research/")
    )
    if research_in_dist:
        errors.append("research files present in CORE_FILES: " + str(research_in_dist))
    if "LICENSE_SCOPE.md" not in core_files:
        errors.append("LICENSE_SCOPE.md is missing from CORE_FILES")

    report: dict[str, Any] = {
        "schema": "boqsc.transvoxel.license_boundary.v1",
        "status": "PASS_LICENSE_BOUNDARY" if not errors else "FAIL_LICENSE_BOUNDARY",
        "report_license": "0BSD",
        "meaning": (
            "Exact oracle-calibrated data is explicitly MIT; generator code, "
            "aggregate-only reports, and the independently derived public core "
            "remain 0BSD."
        ),
        "metrics": {
            "mit_artifact_count": len(EXPECTED_MIT_ARTIFACTS),
            "aggregate_report_count": len(AGGREGATE_REPORTS),
            "public_0bsd_files_scanned": len(public_files),
            "mit_artifacts_in_dist": len(mit_in_dist),
            "research_files_in_dist": len(research_in_dist),
        },
        "mit_artifacts": sorted(EXPECTED_MIT_ARTIFACTS),
        "aggregate_reports": sorted(AGGREGATE_REPORTS),
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)
    print("license boundary:", report["status"])
    for error in errors[:20]:
        print("ERROR", error)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
