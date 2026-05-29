#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Small reader demo for generated/transvoxel_tables.json."""
from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
transvoxel = json.loads((root / "generated" / "transvoxel_tables.json").read_text(encoding="utf-8"))

def read_case(kind: str, case_index: int):
    table = transvoxel[kind]
    cls = table["case_class"][case_index]
    data = table["class_data"][cls]
    vo = data["vertex_offset"]
    to = data["triangle_offset"]
    vc = data["vertex_count"]
    tc = data["triangle_count"]
    vertices = table["vertex_refs"][vo:vo + vc]
    triangles = table["triangles"][to:to + tc]
    return cls, vertices, triangles

for kind, case_index in [("regular", 3), ("transition", 85)]:
    cls, vertices, triangles = read_case(kind, case_index)
    print(f"{kind} case {case_index}: class={cls}, vertices={len(vertices)}, triangles={len(triangles)}")
    print("  first vertices:", vertices[:4])
    print("  first triangles:", triangles[:4])
