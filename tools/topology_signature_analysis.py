#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Derive topology signatures for all 512 transition cases without using external tables.

This is part of the official-equivalence research track. It groups our generated
transition cases by signatures derived only from our 0BSD generated data:

- exact_sample_edge_topology: triangle sets expressed as interpolated sample-edge
  references, with no symmetry reduction.
- d4_sample_edge_topology: same signature canonicalized by square-face D4
  rotations/reflections of the transition-cell sample layout.
- d4_complement_sample_edge_topology: D4 plus inside/outside complement. This is
  the closest no-copy structural comparison to the public "73 classes" fact,
  but it is still not the official class mapping.
- graph_only_topology: an intentionally coarse unlabeled triangle-mesh signature
  using vertex/edge/triangle incidence, not sample positions.

The report never reads Eric Lengyel's MIT-licensed Transvoxel.cpp tables.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation" / "topology_signature_report.json"
MD = ROOT / "validation" / "topology_signature_report.md"
OFFICIAL_CLASS_TARGET = 73

D4 = [
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "mirror_x",
    "mirror_y",
    "transpose",
    "anti_transpose",
]


def load_transition() -> Dict[str, object]:
    path = ROOT / "generated" / "transition_tables.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sample_positions(table: Dict[str, object]) -> Dict[int, Tuple[float, float, float]]:
    out: Dict[int, Tuple[float, float, float]] = {}
    for item in table.get("sample_positions", []):  # type: ignore[union-attr]
        pos = item["position"]
        out[int(item["id"])] = (float(pos[0]), float(pos[1]), float(pos[2]))
    return out


def xy_transform(x: float, y: float, kind: str) -> Tuple[float, float]:
    if kind == "identity":
        return x, y
    if kind == "rot90":
        return 2.0 - y, x
    if kind == "rot180":
        return 2.0 - x, 2.0 - y
    if kind == "rot270":
        return y, 2.0 - x
    if kind == "mirror_x":
        return 2.0 - x, y
    if kind == "mirror_y":
        return x, 2.0 - y
    if kind == "transpose":
        return y, x
    if kind == "anti_transpose":
        return 2.0 - y, 2.0 - x
    raise ValueError(kind)


def build_sample_maps(table: Dict[str, object]) -> Dict[str, Dict[int, int]]:
    pos = sample_positions(table)
    by_pos = {(round(x, 6), round(y, 6), round(z, 6)): sid for sid, (x, y, z) in pos.items()}
    maps: Dict[str, Dict[int, int]] = {}
    for kind in D4:
        mp: Dict[int, int] = {}
        for sid, (x, y, z) in pos.items():
            nx, ny = xy_transform(x, y, kind)
            key = (round(nx, 6), round(ny, 6), round(z, 6))
            if key not in by_pos:
                raise RuntimeError(f"transform {kind} maps sample {sid} to missing position {key}")
            mp[sid] = by_pos[key]
        maps[kind] = mp
    return maps


def build_full_sample_maps(table: Dict[str, object]) -> Dict[str, Dict[int, int]]:
    all_maps = build_sample_maps(table)
    return {k: {sid: mp[sid] for sid in range(9)} for k, mp in all_maps.items()}


def transform_case(case: int, mp: Dict[int, int]) -> int:
    out = 0
    for old in range(9):
        if (case >> old) & 1:
            out |= 1 << mp[old]
    return out


def case_exact_signature(case_data: Dict[str, object]) -> Tuple[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]], ...]:
    verts = [tuple(int(x) for x in v["samples"]) for v in case_data.get("vertices", [])]  # type: ignore[index]
    verts = [tuple(sorted(pair)) for pair in verts]
    tris = []
    for tri in case_data.get("triangles", []):  # type: ignore[union-attr]
        ids = [int(i) for i in tri["vertices"]]
        edge_refs = [verts[i] for i in ids]
        tris.append(tuple(sorted(edge_refs)))
    return tuple(sorted(tris))


def remap_edge(edge: Tuple[int, int], mp: Dict[int, int]) -> Tuple[int, int]:
    return tuple(sorted((mp[edge[0]], mp[edge[1]])))  # type: ignore[return-value]


def transformed_exact_signature(case_data: Dict[str, object], mp: Dict[int, int]) -> Tuple[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]], ...]:
    sig = case_exact_signature(case_data)
    out = []
    for tri in sig:
        out.append(tuple(sorted(remap_edge(edge, mp) for edge in tri)))
    return tuple(sorted(out))


def graph_only_signature(case_data: Dict[str, object]) -> Tuple[object, ...]:
    """Coarse unlabeled topology signature from triangle incidence.

    This is not a full graph-isomorphism solver. It is meant as a conservative
    research metric that can reveal broad topology families without using sample
    labels. Exact official class claims must not be based on this alone.
    """
    verts = case_data.get("vertices", [])
    tris = [[int(i) for i in tri["vertices"]] for tri in case_data.get("triangles", [])]  # type: ignore[union-attr]
    n = len(verts)  # type: ignore[arg-type]
    if not tris:
        return ("empty", n, 0)
    adjacency = [set() for _ in range(n)]
    tri_membership = [0] * n
    edge_count: Counter[Tuple[int, int]] = Counter()
    for tri in tris:
        for v in tri:
            tri_membership[v] += 1
        for a, b in [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]:
            if a > b:
                a, b = b, a
            edge_count[(a, b)] += 1
            adjacency[a].add(b)
            adjacency[b].add(a)
    colors: List[int] = []
    initial_keys = [(len(adjacency[i]), tri_membership[i]) for i in range(n)]
    key_to_id: Dict[Tuple[object, ...], int] = {}
    for key in initial_keys:
        full_key = (key[0], key[1])
        if full_key not in key_to_id:
            key_to_id[full_key] = len(key_to_id)
        colors.append(key_to_id[full_key])
    for _ in range(8):
        new_keys = []
        for i in range(n):
            new_keys.append((colors[i], tuple(sorted(colors[j] for j in adjacency[i]))))
        key_to_id = {}
        new_colors: List[int] = []
        for key in new_keys:
            if key not in key_to_id:
                key_to_id[key] = len(key_to_id)
            new_colors.append(key_to_id[key])
        colors = new_colors
    tri_color_sig = tuple(sorted(tuple(sorted(colors[v] for v in tri)) for tri in tris))
    edge_mult_hist = tuple(sorted(Counter(edge_count.values()).items()))
    return (
        "graph_refine_v2",
        n,
        len(tris),
        tuple(sorted(Counter(colors).items())),
        edge_mult_hist,
        tri_color_sig,
    )


def group_by(items: Iterable[Tuple[int, object]]) -> Dict[str, List[int]]:
    groups: Dict[str, List[int]] = defaultdict(list)
    for case, sig in items:
        groups[repr(sig)].append(case)
    return dict(groups)


def summarize_groups(groups: Dict[str, List[int]]) -> Dict[str, object]:
    sizes = sorted((len(v) for v in groups.values()), reverse=True)
    return {
        "class_count": len(groups),
        "largest_class_size": sizes[0] if sizes else 0,
        "smallest_class_size": sizes[-1] if sizes else 0,
        "size_histogram": dict(sorted(Counter(sizes).items())),
        "representative_cases": [min(v) for v in list(groups.values())[:20]],
    }


def main() -> int:
    table = load_transition()
    cases: List[Dict[str, object]] = table["cases"]  # type: ignore[assignment]
    sample_maps = build_sample_maps(table)
    full_maps = build_full_sample_maps(table)

    exact_groups = group_by((i, case_exact_signature(cases[i])) for i in range(512))

    d4_items = []
    d4_comp_items = []
    # Canonicalize each case by remapping this case's own generated topology.
    # This avoids reading any external table while respecting the transition-cell
    # sample layout used by our generator.
    for i in range(512):
        d4_sigs = [transformed_exact_signature(cases[i], sample_maps[k]) for k in D4]
        d4_items.append((i, min(d4_sigs)))
        comp = i ^ 511
        d4c_sigs = d4_sigs + [transformed_exact_signature(cases[comp], sample_maps[k]) for k in D4]
        d4_comp_items.append((i, min(d4c_sigs)))

    d4_groups = group_by(d4_items)
    d4_comp_groups = group_by(d4_comp_items)
    graph_groups = group_by((i, graph_only_signature(cases[i])) for i in range(512))

    # Also group by canonical target case index under D4/complement, using only
    # bit transforms, to keep continuity with v29's naive orbit report.
    raw_orbit = {}
    for i in range(512):
        orbit = set()
        for mp in full_maps.values():
            tc = transform_case(i, mp)
            orbit.add(tc)
            orbit.add(tc ^ 511)
        raw_orbit[i] = min(orbit)
    raw_groups = group_by((i, raw_orbit[i]) for i in range(512))

    exact_summary = summarize_groups(exact_groups)
    d4_summary = summarize_groups(d4_groups)
    d4_comp_summary = summarize_groups(d4_comp_groups)
    graph_summary = summarize_groups(graph_groups)
    raw_summary = summarize_groups(raw_groups)

    closest = min(
        [
            (abs(int(exact_summary["class_count"]) - OFFICIAL_CLASS_TARGET), "exact_sample_edge_topology", exact_summary),
            (abs(int(d4_summary["class_count"]) - OFFICIAL_CLASS_TARGET), "d4_sample_edge_topology", d4_summary),
            (abs(int(d4_comp_summary["class_count"]) - OFFICIAL_CLASS_TARGET), "d4_complement_sample_edge_topology", d4_comp_summary),
            (abs(int(graph_summary["class_count"]) - OFFICIAL_CLASS_TARGET), "graph_only_topology", graph_summary),
            (abs(int(raw_summary["class_count"]) - OFFICIAL_CLASS_TARGET), "raw_d4_complement_orbit", raw_summary),
        ],
        key=lambda x: x[0],
    )
    official_match = any(int(s["class_count"]) == OFFICIAL_CLASS_TARGET for _, _, s in [
        (0, "exact", exact_summary),
        (0, "d4", d4_summary),
        (0, "d4c", d4_comp_summary),
        (0, "graph", graph_summary),
        (0, "raw", raw_summary),
    ])
    status = "RESEARCH_PASS_TOPOLOGY_CLASSES_DERIVED_OFFICIAL_EQUIVALENCE_NOT_PROVEN"
    report = {
        "schema": "boqsc.transvoxel.topology_signature_analysis.v1",
        "status": status,
        "official_class_target": OFFICIAL_CLASS_TARGET,
        "official_equivalence_proof": "NOT_PROVEN",
        "no_copy_boundary": {
            "external_table_values_read": False,
            "external_table_values_used_as_golden_output": False,
            "inputs": ["generated/transition_tables.json"],
        },
        "class_summaries": {
            "exact_sample_edge_topology": exact_summary,
            "d4_sample_edge_topology": d4_summary,
            "d4_complement_sample_edge_topology": d4_comp_summary,
            "graph_only_topology_coarse": graph_summary,
            "raw_d4_complement_orbit": raw_summary,
        },
        "closest_count_to_official_target": {
            "name": closest[1],
            "class_count": closest[2]["class_count"],
            "distance_from_73": closest[0],
        },
        "matches_official_73_count": official_match,
        "interpretation": [
            "This project's generated topology classes do not prove official Transvoxel 73-class equivalence.",
            "If none of the topology signature counts equals 73, the current tetrahedralized transition topology is structurally different from the official 73-class table design, or the official classes depend on a richer equivalence relation not represented by these signatures.",
            "Even if a count equaled 73, that would still be only a structural clue, not proof of matching official class IDs or triangle encodings.",
        ],
        "limitations": [
            "graph_only_topology is a coarse color-refinement signature, not a formal graph-isomorphism proof.",
            "sample-edge topology uses midpoint/sample-edge references from this generator, not arbitrary density interpolation positions.",
            "No official MIT table values are loaded, compared, or copied.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Topology Signature Analysis",
        "",
        f"Status: **{status}**",
        "",
        f"Official class target: `{OFFICIAL_CLASS_TARGET}`",
        "",
        "## Class counts",
        "",
    ]
    for name, summary in report["class_summaries"].items():
        lines.append(f"- `{name}`: `{summary['class_count']}` classes")
    lines += [
        "",
        "## Closest count",
        "",
        f"- `{closest[1]}`: `{closest[2]['class_count']}` classes, distance `{closest[0]}` from 73",
        "",
        "## Interpretation",
        "",
    ]
    lines += [f"- {x}" for x in report["interpretation"]]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in report["limitations"]] + [""]
    MD.write_text("\n".join(lines), encoding="utf-8")
    print("topology signature analysis:", status)
    print("closest-to-73:", closest[1], closest[2]["class_count"], "classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
