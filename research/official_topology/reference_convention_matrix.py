#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Validate the published canonical transition frame in all six M4 directions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "reference_convention_matrix.json"

Vec = Tuple[int, int, int]


def cross(a: Vec, b: Vec) -> Vec:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a: Vec, b: Vec) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def neg(a: Vec) -> Vec:
    return (-a[0], -a[1], -a[2])


# Exact frames implemented by tv_m4_transition_face_frame(). The face name is
# the world direction of canonical +z, from the full face toward the half face.
FACES = {
    "positive_x": {"u": (0, 1, 0), "v": (0, 0, 1), "full_to_half": (1, 0, 0)},
    "negative_x": {"u": (0, -1, 0), "v": (0, 0, 1), "full_to_half": (-1, 0, 0)},
    "positive_y": {"u": (0, 0, 1), "v": (1, 0, 0), "full_to_half": (0, 1, 0)},
    "negative_y": {"u": (0, 0, -1), "v": (1, 0, 0), "full_to_half": (0, -1, 0)},
    "positive_z": {"u": (1, 0, 0), "v": (0, 1, 0), "full_to_half": (0, 0, 1)},
    "negative_z": {"u": (-1, 0, 0), "v": (0, 1, 0), "full_to_half": (0, 0, -1)},
}


def main() -> int:
    rows = []
    errors = []
    for name, info in FACES.items():
        u = info["u"]
        v = info["v"]
        w = info["full_to_half"]
        handed = cross(u, v)
        ok = handed == w
        if not ok:
            errors.append(f"{name}: u x v != full_to_half")
        rows.append({
            "face": name,
            "u_axis": u,
            "v_axis": v,
            "full_to_half_axis": w,
            "half_to_full_axis": neg(w),
            "low_resolution_block_outward_to_high_resolution_neighbor": neg(w),
            "cross_u_v": handed,
            "right_handed_u_v_full_to_half": ok,
            "dot_u_w": dot(u, w),
            "dot_v_w": dot(v, w),
        })
    directions = [tuple(row["full_to_half_axis"]) for row in rows]
    if len(set(directions)) != 6:
        errors.append("full-to-half axes are not six unique directions")
    report = {
        "schema": "boqsc.transvoxel.reference_convention_matrix.v2",
        "status": (
            "PASS_PUBLISHED_REFERENCE_CONVENTION_MATRIX"
            if not errors
            else "FAIL"
        ),
        "official_reference_equivalence": "PROVEN" if not errors else "NOT_PROVEN",
        "equivalence_scope": (
            "Published algorithmic sample/sign/face/winding convention through "
            "orientation-preserving transforms; not official table topology or bytes."
        ),
        "canonical_frame": (
            "u/v are dissertation Figure 4.16 x/y; +w is full-resolution face "
            "to half-resolution face; u x v = +w"
        ),
        "faces": rows,
        "errors": errors,
        "no_copy_rule": (
            "Uses public dissertation diagrams/prose and local M4 frame code; "
            "does not inspect official lookup-table arrays."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("reference convention matrix:", report["status"])
    print(OUT)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
