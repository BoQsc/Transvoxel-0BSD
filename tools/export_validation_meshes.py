#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Export OBJ meshes for visual inspection of generated transition cases."""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

Vec3 = Tuple[float, float, float]

EPS = 1.0e-12


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_generator():
    path = root_dir() / "tools" / "generate_transition.py"
    spec = importlib.util.spec_from_file_location("generate_transition_tables", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interp(pa: Vec3, pb: Vec3, va: float, vb: float) -> Vec3:
    denom = va - vb
    if abs(denom) < EPS:
        t = 0.5
    else:
        t = va / denom
    return (
        pa[0] + (pb[0] - pa[0]) * t,
        pa[1] + (pb[1] - pa[1]) * t,
        pa[2] + (pb[2] - pa[2]) * t,
    )


def value_for_case(gen, case_index: int, sample_id: int) -> float:
    return -1.0 if gen.sign_for_sample(case_index, sample_id) else 1.0


def case_mesh_from_signs(gen, case_index: int) -> Tuple[List[Vec3], List[Tuple[int, int, int]]]:
    table = gen.generate_tables()
    case = table["cases"][case_index]
    verts: List[Vec3] = []
    for vertex in case["vertices"]:
        a, b = [int(x) for x in vertex["samples"]]
        pa = tuple(float(x) for x in gen.SAMPLE_POSITIONS[a])
        pb = tuple(float(x) for x in gen.SAMPLE_POSITIONS[b])
        va = value_for_case(gen, case_index, a)
        vb = value_for_case(gen, case_index, b)
        verts.append(interp(pa, pb, va, vb))
    tris = [tuple(int(x) for x in tri["vertices"]) for tri in case["triangles"]]
    return verts, tris


def write_obj(path: Path, vertices: List[Vec3], triangles: List[Tuple[int, int, int]], comment: str) -> None:
    lines = []
    lines.append("# SPDX-License-Identifier: 0BSD")
    lines.append("# " + comment)
    for v in vertices:
        lines.append("v %.9f %.9f %.9f" % v)
    for a, b, c in triangles:
        lines.append("f %d %d %d" % (a + 1, b + 1, c + 1))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_cases(gen, out_dir: Path, case_ids: List[int]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for case_index in case_ids:
        vertices, triangles = case_mesh_from_signs(gen, case_index)
        path = out_dir / ("case_%03d.obj" % case_index)
        write_obj(path, vertices, triangles, "Clean-room transition table case %d" % case_index)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="validation/obj_cases")
    parser.add_argument(
        "--cases",
        default="1,2,3,7,15,31,63,85,127,170,255,341,383,447,510",
        help="Comma-separated case ids to export",
    )
    args = parser.parse_args()

    gen = load_generator()
    case_ids = []
    for part in args.cases.split(","):
        part = part.strip()
        if not part:
            continue
        case_id = int(part)
        if not 0 <= case_id < 512:
            raise SystemExit("case id out of range: %s" % case_id)
        case_ids.append(case_id)

    out_dir = root_dir() / args.out
    export_cases(gen, out_dir, case_ids)
    print("wrote OBJ validation cases:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
