#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "validation" / "github_ready_report.json"

REQUIRED_FILES = [
    "README.md",
    "README_CORE.txt",
    "CHANGELOG.md",
    "LICENSE",
    "PROVENANCE.md",
    "SOURCES.md",
    "VERSION",
    ".gitignore",
    ".github/workflows/core.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/correctness_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    "docs/GITHUB_RELEASE_PAGE.md",
    "docs/GITHUB_PUBLISHING.md",
    "docs/REPOSITORY_LAYOUT.md",
    "docs/PUBLIC_RELEASE.md",
    "docs/KNOWN_LIMITS.md",
    "docs/WHAT_THIS_PROVES.md",
    "docs/API.md",
    "docs/DROP_IN.md",
    "docs/CORE_PACKAGE_CONTENTS.md",
    "docs/PROJECT_TRACKS.md",
    "include/transvoxel.h",
    "src/transvoxel.c",
    "generated/transvoxel_tables.h",
    "examples/c_minimal/main.c",
    "examples/c_terrain_export/main.c",
    "dist/transvoxel_0bsd_core.zip",
]

FORBIDDEN_TRACKED_OUTPUTS = [
    "proof/SEND_TO_CHATGPT.zip",
    "proof/c_compiler_cache.json",
    "proof/one_click_log.txt",
]


def main() -> int:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]
    forbidden_present = [rel for rel in FORBIDDEN_TRACKED_OUTPUTS if (ROOT / rel).exists()]
    version = (ROOT / "VERSION").read_text(encoding="utf-8", errors="replace").strip() if (ROOT / "VERSION").exists() else "<missing>"
    report = {
        "schema": "boqsc.transvoxel.github_ready_report.v1",
        "version": version,
        "status": "PASS" if not missing and not forbidden_present else "FAIL",
        "missing": missing,
        "forbidden_present": forbidden_present,
        "notes": [
            "This checks repository publishing files only.",
            "It does not rerun Godot runtime validation.",
            "Official Transvoxel.cpp / 73-class equivalence remains NOT_PROVEN unless separately proven by the research track.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("github ready:", report["status"])
    if missing:
        print("missing:", missing)
    if forbidden_present:
        print("forbidden present:", forbidden_present)
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
