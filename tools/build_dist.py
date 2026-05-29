#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
CORE_DIR = DIST / "transvoxel_0bsd_core"
CORE_ZIP = DIST / "transvoxel_0bsd_core.zip"
REPORT = ROOT / "validation" / "dist_report.json"

CORE_FILES = [
    "LICENSE",
    "README_CORE.txt",
    "PROVENANCE.md",
    "SOURCES.md",
    "docs/DROP_IN.md",
    "docs/API.md",
    "docs/C_COMPILER.md",
    "docs/WHAT_THIS_PROVES.md",
    "docs/CORE_PACKAGE_CONTENTS.md",
    "docs/KNOWN_LIMITS.md",
    "include/transvoxel.h",
    "src/transvoxel.c",
    "generated/transvoxel_tables.h",
    "examples/c_minimal/main.c",
    "examples/c_minimal/BUILD_WITH_ZIG.cmd",
    "examples/c_minimal/BUILD_WITH_CC.sh",
    "examples/c_terrain_export/main.c",
    "examples/c_terrain_export/README.md",
    "examples/c_terrain_export/BUILD_WITH_ZIG.cmd",
    "examples/c_terrain_export/BUILD_WITH_CC.sh",
]


def copy_file(rel: str) -> None:
    src = ROOT / rel
    dst = CORE_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    if CORE_DIR.exists():
        shutil.rmtree(CORE_DIR)
    CORE_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    missing = []
    for rel in CORE_FILES:
        if (ROOT / rel).exists():
            copy_file(rel)
            copied.append(rel)
        else:
            missing.append(rel)

    if CORE_ZIP.exists():
        CORE_ZIP.unlink()
    with zipfile.ZipFile(CORE_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(CORE_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, str(path.relative_to(DIST)))

    report = {
        "schema": "boqsc.transvoxel.dist_report.v5",
        "status": "PASS" if not missing else "FAIL",
        "core_zip": str(CORE_ZIP),
        "copied": copied,
        "missing": missing,
        "note": "Minimal core zip intentionally excludes generated JSON proof data. Use the full repository package for generator/proof data.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("dist core zip:", CORE_ZIP)
    print("dist:", report["status"])
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
