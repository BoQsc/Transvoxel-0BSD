#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
import subprocess
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
    "RUN_M10.cmd",
    "RUN_M11.cmd",
    "RUN_M12.cmd",
    "include/transvoxel.h",
    "include/transvoxel_m4_candidate.h",
    "include/transvoxel_m4_backend.h",
    "src/transvoxel.c",
    "src/transvoxel_m4_candidate.c",
    "src/transvoxel_m4_backend.c",
    "generated/transvoxel_tables.h",
    "generated/official_topology_candidate_tables.h",
    "examples/c_minimal/main.c",
    "examples/c_terrain_export/main.c",
    "examples/c_m4_backend_switch/main.c",
    "tools/test_m4_backend_c.py",
    "tools/test_m4_terrain_c.py",
    "tools/validate_m4_godot_candidate.py",
    "tools/validate_m4_godot_viewer.py",
    "tools/validate_m4_godot_backend_compare.py",
    "godot/generated/official_topology_candidate_tables.json",
    "godot/stages/05_m4_candidate_metrics/DumpM4CandidateMetrics.gd",
    "godot/stages/05_m4_candidate_metrics/README.md",
    "godot/stages/08_m4_candidate_viewer/DumpM4CandidateViewer.gd",
    "godot/stages/08_m4_candidate_viewer/README.md",
    "godot/stages/09_m4_backend_compare/DumpM4BackendCompare.gd",
    "godot/stages/09_m4_backend_compare/README.md",
    "dist/transvoxel_0bsd_core.zip",
]

# These files may be created locally by RUN.cmd / test_core_c.py, but they must not
# be committed to the repository or shipped as repository source files.
FORBIDDEN_REPOSITORY_FILES = [
    "proof/SEND_TO_CHATGPT.zip",
    "proof/c_compiler_cache.json",
    "proof/one_click_log.txt",
    "proof/one_click_report.json",
    "proof/ONE_CLICK_RESULT.txt",
]


def _git_tracked_files() -> tuple[set[str] | None, str | None]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except Exception as exc:
        return None, f"git ls-files unavailable: {exc}"
    if proc.returncode != 0:
        return None, proc.stderr.strip() or "git ls-files returned non-zero status"
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}, None


def main() -> int:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]
    tracked, git_warning = _git_tracked_files()
    if tracked is None:
        forbidden_tracked: list[str] = []
        local_forbidden_present = [rel for rel in FORBIDDEN_REPOSITORY_FILES if (ROOT / rel).exists()]
        notes = [
            "This checks repository publishing files only.",
            "git ls-files was unavailable, so forbidden tracked-file detection was skipped.",
            "Local generated proof files may exist after a run; they are ignored by .gitignore and should not be committed.",
            "Official Transvoxel.cpp / 73-class equivalence remains NOT_PROVEN unless separately proven by the research track.",
        ]
    else:
        forbidden_tracked = [rel for rel in FORBIDDEN_REPOSITORY_FILES if rel in tracked]
        local_forbidden_present = [rel for rel in FORBIDDEN_REPOSITORY_FILES if (ROOT / rel).exists()]
        notes = [
            "This checks repository publishing files only.",
            "Forbidden proof/cache files are checked against git-tracked files, not local generated files.",
            "Local generated proof files may exist after a run; they are ignored by .gitignore and should not be committed.",
            "Official Transvoxel.cpp / 73-class equivalence remains NOT_PROVEN unless separately proven by the research track.",
        ]
    version = (ROOT / "VERSION").read_text(encoding="utf-8", errors="replace").strip() if (ROOT / "VERSION").exists() else "<missing>"
    report = {
        "schema": "boqsc.transvoxel.github_ready_report.v2",
        "version": version,
        "status": "PASS" if not missing and not forbidden_tracked else "FAIL",
        "missing": missing,
        "forbidden_tracked": forbidden_tracked,
        "local_forbidden_present_ignored": local_forbidden_present,
        "git_warning": git_warning,
        "notes": notes,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("github ready:", report["status"])
    if missing:
        print("missing:", missing)
    if forbidden_tracked:
        print("forbidden tracked:", forbidden_tracked)
        print("Remove them with: git rm --cached " + " ".join(forbidden_tracked))
    if local_forbidden_present and not forbidden_tracked:
        print("local generated files ignored:", local_forbidden_present)
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
