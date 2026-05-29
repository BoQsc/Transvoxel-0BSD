#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "generated"
DST = ROOT / "godot" / "generated"
NAMES = ["regular_tables.json", "transition_tables.json", "transvoxel_tables.json"]


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        src = SRC / name
        dst = DST / name
        if not src.exists():
            print("godot table sync: FAIL")
            print("missing", src.relative_to(ROOT))
            return 1
        shutil.copyfile(src, dst)
        print("synced", dst.relative_to(ROOT))
    print("godot table sync: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
