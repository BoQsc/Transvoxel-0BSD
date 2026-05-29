#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""No-copy candidate research toward the official 73 transition classes.

This script does not read Eric Lengyel's MIT table arrays. It enumerates the
512 transition face sign patterns, computes symmetry orbits, detects ambiguous
2x2 subfaces, and reports how close several first-principles grouping models
come to the public 73-class target.

The important output is negative/diagnostic: if a model reaches 73, it is only a
candidate requiring independent topology, winding, and seam proof. It is never
treated as official equivalence by itself.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "validation" / "official_73_candidate_derivation.json"
OUT_MD = ROOT / "validation" / "official_73_candidate_derivation.md"
OFFICIAL_TARGET = 73

COORDS = [(i % 3, i // 3) for i in range(9)]
INDEX = {(x, y): y * 3 + x for x in range(3) for y in range(3)}
SQUARES = [
    (0, 1, 4, 3),
    (1, 2, 5, 4),
    (3, 4, 7, 6),
    (4, 5, 8, 7),
]


def rot_coord(x: int, y: int, k: int) -> tuple[int, int]:
    for _ in range(k % 4):
        x, y = 2 - y, x
    return x, y


def transform_coord(x: int, y: int, t: int) -> tuple[int, int]:
    if t >= 4:
        x = 2 - x
    return rot_coord(x, y, t % 4)


def make_perms(kind: str) -> list[list[int]]:
    if kind == "c4":
        return [[INDEX[rot_coord(x, y, k)] for x, y in COORDS] for k in range(4)]
    if kind == "d4":
        return [[INDEX[transform_coord(x, y, t)] for x, y in COORDS] for t in range(8)]
    raise ValueError(kind)


def apply_perm(case: int, perm: list[int]) -> int:
    out = 0
    for old, new in enumerate(perm):
        if (case >> old) & 1:
            out |= 1 << new
    return out


def canonical(case: int, perms: list[list[int]], complement: bool) -> int:
    vals = []
    for p in perms:
        vals.append(apply_perm(case, p))
        if complement:
            vals.append(apply_perm(case ^ 0x1FF, p))
    return min(vals)


def bits(case: int, indices: Iterable[int]) -> tuple[int, ...]:
    return tuple((case >> i) & 1 for i in indices)


def ambiguous_square_mask(case: int) -> tuple[int, int, int, int]:
    out: list[int] = []
    for sq in SQUARES:
        b = bits(case, sq)
        out.append(1 if (b[0] == b[2] and b[1] == b[3] and b[0] != b[1]) else 0)
    return tuple(out)  # type: ignore[return-value]


def sign_change_edge_count(case: int) -> int:
    edges = set()
    # horizontal and vertical edges in the 3x3 sample grid
    for y in range(3):
        for x in range(2):
            a = INDEX[(x, y)]
            b = INDEX[(x + 1, y)]
            if ((case >> a) & 1) != ((case >> b) & 1):
                edges.add(tuple(sorted((a, b))))
    for y in range(2):
        for x in range(3):
            a = INDEX[(x, y)]
            b = INDEX[(x, y + 1)]
            if ((case >> a) & 1) != ((case >> b) & 1):
                edges.add(tuple(sorted((a, b))))
    return len(edges)


def connected_components(case: int, value: int, diagonal: bool = False) -> int:
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen: set[int] = set()
    comps = 0
    for i, (x, y) in enumerate(COORDS):
        if ((case >> i) & 1) != value or i in seen:
            continue
        comps += 1
        stack = [i]
        seen.add(i)
        while stack:
            cur = stack.pop()
            cx, cy = COORDS[cur]
            for dx, dy in dirs:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < 3 and 0 <= ny < 3:
                    ni = INDEX[(nx, ny)]
                    if ni not in seen and ((case >> ni) & 1) == value:
                        seen.add(ni)
                        stack.append(ni)
    return comps


def feature(case: int, name: str):
    amb = ambiguous_square_mask(case)
    if name == "none":
        return ()
    if name == "ambiguous_square_count":
        return (sum(amb),)
    if name == "sign_change_edges":
        return (sign_change_edge_count(case),)
    if name == "inside_count_unsigned":
        return (min(case.bit_count(), 9 - case.bit_count()),)
    if name == "components4_unsigned":
        a = connected_components(case, 1, False)
        b = connected_components(case, 0, False)
        return (min(a, b), max(a, b))
    if name == "components8_unsigned":
        a = connected_components(case, 1, True)
        b = connected_components(case, 0, True)
        return (min(a, b), max(a, b))
    if name == "ambiguous_plus_edges":
        return (sum(amb), sign_change_edge_count(case))
    if name == "ambiguous_plus_components":
        a = connected_components(case, 1, False)
        b = connected_components(case, 0, False)
        return (sum(amb), min(a, b), max(a, b))
    raise ValueError(name)


def count_model(symmetry: str, complement: bool, feature_name: str) -> dict:
    perms = make_perms(symmetry)
    groups: dict[tuple[int, object], list[int]] = defaultdict(list)
    for case in range(512):
        key = (canonical(case, perms, complement), feature(case, feature_name))
        groups[key].append(case)
    return {
        "symmetry": symmetry,
        "complement": complement,
        "feature": feature_name,
        "class_count": len(groups),
        "distance_from_73": abs(len(groups) - OFFICIAL_TARGET),
        "sample_classes": [
            {"key": str(k), "size": len(v), "cases": v[:16]}
            for k, v in sorted(groups.items(), key=lambda kv: (len(kv[1]), str(kv[0])))[:12]
        ],
    }


def c4_complement_orbits() -> dict[int, list[int]]:
    perms = make_perms("c4")
    out: dict[int, list[int]] = defaultdict(list)
    for case in range(512):
        out[canonical(case, perms, True)].append(case)
    return dict(out)


def split_candidate_orbits() -> list[dict]:
    # Public fact: target 73. No-copy observation: C4+complement gives 70.
    # Therefore an exact first-principles candidate would have to split 3 raw
    # C4+complement orbits, or use a different operation set entirely.
    orbits = c4_complement_orbits()
    candidates = []
    for key, cases in sorted(orbits.items()):
        amb_counts = sorted({sum(ambiguous_square_mask(c)) for c in cases})
        edge_counts = sorted({sign_change_edge_count(c) for c in cases})
        if max(amb_counts or [0]) > 0:
            candidates.append({
                "orbit_key": key,
                "size": len(cases),
                "ambiguous_square_counts": amb_counts,
                "sign_change_edge_counts": edge_counts,
                "cases": cases[:32],
                "reason_for_attention": "contains at least one ambiguous 2x2 high-resolution face pattern",
            })
    # Rank smaller/more constrained candidates first.
    candidates.sort(key=lambda x: (len(x["ambiguous_square_counts"]), x["size"], x["orbit_key"]))
    return candidates


def main() -> int:
    models = []
    for symmetry in ["c4", "d4"]:
        for comp in [False, True]:
            for feat in [
                "none",
                "ambiguous_square_count",
                "sign_change_edges",
                "inside_count_unsigned",
                "components4_unsigned",
                "components8_unsigned",
                "ambiguous_plus_edges",
                "ambiguous_plus_components",
            ]:
                models.append(count_model(symmetry, comp, feat))
    models.sort(key=lambda m: (m["distance_from_73"], m["class_count"], m["symmetry"], str(m["complement"]), m["feature"]))
    closest = models[0]
    report = {
        "schema": "boqsc.transvoxel.official_73_candidate_derivation.v1",
        "status": "RESEARCH_PASS_OFFICIAL_73_NOT_DERIVED",
        "official_target_class_count": OFFICIAL_TARGET,
        "no_copy_rule": "No official MIT table arrays are read, transcribed, hashed, compared, or used as golden output.",
        "model_count": len(models),
        "closest_model": closest,
        "models": models,
        "c4_complement_raw_class_count": len(c4_complement_orbits()),
        "minimum_split_observation": "A C4+complement raw sign-pattern model gives 70 classes, so reaching 73 from that model would require exactly three principled orbit splits, or a different topology-level equivalence definition.",
        "ambiguous_orbit_split_candidates": split_candidate_orbits()[:25],
        "verdict": "No implemented no-copy model in this script derives the official 73-class mapping. The script narrows the next research question to principled splits of ambiguous high-resolution face topology and/or a different topology-level equivalence definition.",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Official 73-Class Candidate Derivation",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Official target class count: **{OFFICIAL_TARGET}**",
        f"Closest no-copy model: **{closest['class_count']} classes** using `{closest['symmetry']}`, complement={closest['complement']}, feature=`{closest['feature']}`.",
        "",
        "## Important result",
        "",
        report["minimum_split_observation"],
        "",
        "## No-copy boundary",
        "",
        report["no_copy_rule"],
        "",
        "## Verdict",
        "",
        report["verdict"],
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("official 73 candidate derivation:", report["status"])
    print("closest:", closest["class_count"], "classes")
    print(OUT_JSON)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
