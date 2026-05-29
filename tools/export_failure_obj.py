#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Export OBJ meshes for failed transition cases.

If validation reports contain failing case ids, this script exports those cases
for visual inspection. If there are no failures, it writes a small note and can
optionally export representative cases with --representative.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Set

ROOT = Path(__file__).resolve().parents[1]


def collect_cases_from_report(path: Path) -> Set[int]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: Set[int] = set()
    for key in ("failures", "first_determinism_failures", "first_opposite_face_failures"):
        for item in data.get(key, []) or []:
            if isinstance(item, dict):
                if "case" in item:
                    cases.add(int(item["case"]))
                if "case_a" in item:
                    cases.add(int(item["case_a"]))
                if "case_b" in item:
                    cases.add(int(item["case_b"]))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="validation/failure_obj")
    parser.add_argument("--representative", action="store_true")
    args = parser.parse_args()

    report_paths = [
        ROOT / "validation" / "boundary_report.json",
        ROOT / "validation" / "neighbor_report.json",
        ROOT / "validation" / "chunk_report.json",
    ]
    cases: Set[int] = set()
    for path in report_paths:
        cases.update(collect_cases_from_report(path))

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if not cases and args.representative:
        cases.update([1, 2, 3, 7, 15, 31, 63, 85, 127, 170, 255, 341, 383, 447, 510])

    if not cases:
        (out_dir / "README.md").write_text(
            "# Failure OBJ exports\n\nNo failed cases were found in the current validation reports.\n",
            encoding="utf-8",
        )
        print("no failed cases found")
        return 0

    case_arg = ",".join(str(c) for c in sorted(cases))
    cmd = [sys.executable, str(ROOT / "tools" / "export_validation_meshes.py"), "--out", args.out, "--cases", case_arg]
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
