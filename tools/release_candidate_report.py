#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "validation" / "release_candidate_report.json"
CORE_ZIP = ROOT / "dist" / "transvoxel_0bsd_core.zip"

REQUIRED = {
    "transvoxel_0bsd_core/LICENSE",
    "transvoxel_0bsd_core/LICENSE_SCOPE.md",
    "transvoxel_0bsd_core/README_CORE.txt",
    "transvoxel_0bsd_core/PROVENANCE.md",
    "transvoxel_0bsd_core/SOURCES.md",
    "transvoxel_0bsd_core/include/transvoxel.h",
    "transvoxel_0bsd_core/include/transvoxel_m4_candidate.h",
    "transvoxel_0bsd_core/include/transvoxel_m4_backend.h",
    "transvoxel_0bsd_core/src/transvoxel.c",
    "transvoxel_0bsd_core/src/transvoxel_m4_candidate.c",
    "transvoxel_0bsd_core/src/transvoxel_m4_backend.c",
    "transvoxel_0bsd_core/generated/transvoxel_tables.h",
    "transvoxel_0bsd_core/generated/official_topology_candidate_tables.h",
    "transvoxel_0bsd_core/examples/c_minimal/main.c",
    "transvoxel_0bsd_core/examples/c_terrain_export/main.c",
    "transvoxel_0bsd_core/examples/c_m4_backend_switch/main.c",
    "transvoxel_0bsd_core/examples/c_m4_backend_switch/BUILD_WITH_ZIG.cmd",
    "transvoxel_0bsd_core/examples/c_m4_backend_switch/BUILD_WITH_CC.sh",
    "transvoxel_0bsd_core/examples/c_m21_consumer_contract/main.c",
    "transvoxel_0bsd_core/examples/cpp_consumer/main.cpp",
    "transvoxel_0bsd_core/docs/API.md",
    "transvoxel_0bsd_core/docs/DROP_IN.md",
    "transvoxel_0bsd_core/docs/WHAT_THIS_PROVES.md",
    "transvoxel_0bsd_core/docs/C_COMPILER.md",
    "transvoxel_0bsd_core/docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md",
    "transvoxel_0bsd_core/docs/CORE_PACKAGE_CONTENTS.md",
    "transvoxel_0bsd_core/docs/KNOWN_LIMITS.md",
    "transvoxel_0bsd_core/docs/TESTING_BY_USERS.md",
}

FORBIDDEN_PARTS = [
    "/proof/",
    "/runs/",
    "/godot/",
    "/research/",
    "/validation/",
    "SEND_TO_CHATGPT.zip",
    "c_compiler_cache.json",
    "one_click_log.txt",
    "production_gate.json",
]


def main() -> int:
    report = {
        "schema": "boqsc.transvoxel.release_candidate_report.v1",
        "core_zip": str(CORE_ZIP),
        "status": "FAIL",
        "missing": [],
        "forbidden": [],
        "file_count": 0,
        "notes": [
            "This checks the small public core zip, not the full proof repository package.",
            "Official Transvoxel.cpp / 73-class equivalence remains NOT_PROVEN by design.",
        ],
    }
    if not CORE_ZIP.exists():
        report["missing"] = ["dist/transvoxel_0bsd_core.zip"]
    else:
        with zipfile.ZipFile(CORE_ZIP, "r") as zf:
            names = set(zf.namelist())
        report["file_count"] = len(names)
        report["missing"] = sorted(REQUIRED - names)
        forbidden = []
        for name in sorted(names):
            norm = "/" + name.replace("\\", "/")
            for part in FORBIDDEN_PARTS:
                if part in norm or norm.endswith("/" + part):
                    forbidden.append(name)
                    break
        report["forbidden"] = forbidden
    report["status"] = "PASS" if not report["missing"] and not report["forbidden"] else "FAIL"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("release candidate:", report["status"])
    if report["missing"]:
        print("missing:", report["missing"])
    if report["forbidden"]:
        print("forbidden:", report["forbidden"][:20])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
