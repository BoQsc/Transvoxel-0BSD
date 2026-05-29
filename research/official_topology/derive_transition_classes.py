#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""No-copy research scaffold for transition class derivation.

This script intentionally does not read official Transvoxel table values.
It reports known no-copy grouping attempts and marks the official 73-class
mapping as a research target, not a proven result.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "official_transition_class_derivation.json"

def main() -> int:
    topology_report = ROOT / "validation" / "topology_signature_report.json"
    topology = {}
    if topology_report.exists():
        topology = json.loads(topology_report.read_text(encoding="utf-8"))
    report = {
        "schema": "boqsc.transvoxel.official_transition_class_derivation.v1",
        "status": "RESEARCH_TARGET_NOT_PROVEN",
        "official_target_class_count": 73,
        "no_copy_rule": "Does not read official MIT table arrays or use them as golden output.",
        "current_known_counts": {
            "raw_d4_complement_orbit": topology.get("raw_d4_complement_orbit", {}).get("class_count"),
            "exact_sample_edge_topology": topology.get("exact_sample_edge_topology", {}).get("class_count"),
            "d4_sample_edge_topology": topology.get("d4_sample_edge_topology", {}).get("class_count"),
            "d4_complement_sample_edge_topology": topology.get("d4_complement_sample_edge_topology", {}).get("class_count"),
            "graph_only_topology_coarse": topology.get("graph_only_topology_coarse", {}).get("class_count"),
        },
        "verdict": "Current independent generator has not derived the official 73-class mapping.",
        "next_steps": [
            "derive official-style transition topology from paper diagrams / first principles",
            "define a topology signature that can collapse to 73 without reading table values",
            "prove orientation/sign convention separately",
            "run the same production gate on any official-style candidate core",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("official transition class derivation:", report["status"])
    print(OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
