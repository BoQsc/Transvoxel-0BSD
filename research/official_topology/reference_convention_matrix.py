#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Build an internal reference-orientation matrix for transition faces.

This is not proof that the project matches Eric Lengyel's MIT table convention.
It is a no-copy prerequisite: before comparing conventions, the project must
state its own high/low face, tangent axes, normal direction, and handedness for
all six chunk faces.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "reference_convention_matrix.json"

Vec = Tuple[int, int, int]

def cross(a: Vec, b: Vec) -> Vec:
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def dot(a: Vec, b: Vec) -> int:
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]

def neg(a: Vec) -> Vec:
    return (-a[0], -a[1], -a[2])

# Internal convention: transition face normal points from the low-resolution
# chunk toward the high-resolution neighbor. u/v form a right-handed frame with
# n: u x v = n.
FACES = {
    "x_pos": {"normal_low_to_high": (1, 0, 0), "u": (0, 1, 0), "v": (0, 0, 1)},
    "x_neg": {"normal_low_to_high": (-1, 0, 0), "u": (0, 0, 1), "v": (0, 1, 0)},
    "y_pos": {"normal_low_to_high": (0, 1, 0), "u": (0, 0, 1), "v": (1, 0, 0)},
    "y_neg": {"normal_low_to_high": (0, -1, 0), "u": (1, 0, 0), "v": (0, 0, 1)},
    "z_pos": {"normal_low_to_high": (0, 0, 1), "u": (1, 0, 0), "v": (0, 1, 0)},
    "z_neg": {"normal_low_to_high": (0, 0, -1), "u": (0, 1, 0), "v": (1, 0, 0)},
}


def main() -> int:
    face_rows = []
    errors = []
    for name, info in FACES.items():
        n = info["normal_low_to_high"]
        u = info["u"]
        v = info["v"]
        handed = cross(u, v)
        ok = handed == n
        if not ok:
            errors.append(f"{name}: u x v != normal")
        face_rows.append({
            "face": name,
            "normal_low_to_high": n,
            "normal_high_to_low": neg(n),
            "u_axis": u,
            "v_axis": v,
            "cross_u_v": handed,
            "right_handed_u_v_n": ok,
            "dot_u_n": dot(u, n),
            "dot_v_n": dot(v, n),
        })
    normals = [tuple(row["normal_low_to_high"]) for row in face_rows]
    if len(set(normals)) != 6:
        errors.append("face normals are not six unique axis directions")
    report = {
        "schema": "boqsc.transvoxel.reference_convention_matrix.v1",
        "status": "PASS_INTERNAL_CONVENTION_MATRIX" if not errors else "FAIL",
        "official_reference_equivalence": "NOT_PROVEN",
        "no_copy_rule": "This matrix defines our internal convention only; it does not read or compare official MIT table values.",
        "convention": "normal points from low-resolution chunk toward high-resolution neighbor; u x v = normal",
        "faces": face_rows,
        "errors": errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("reference convention matrix:", report["status"])
    print(OUT)
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
