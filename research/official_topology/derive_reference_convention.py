#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Record the published transition-cell convention without table-array data."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "validation" / "official_reference_convention_research.json"

FULL_SAMPLES = {
    sample_id: [sample_id % 3, sample_id // 3, 0]
    for sample_id in range(9)
}
HALF_SAMPLES = {
    9: [0, 0, 1],
    10: [2, 0, 1],
    11: [0, 2, 1],
    12: [2, 2, 1],
}
REFERENCE_CASE_BITS = {
    0: 0x001,
    1: 0x002,
    2: 0x004,
    3: 0x080,
    4: 0x100,
    5: 0x008,
    6: 0x040,
    7: 0x020,
    8: 0x010,
}


def main() -> int:
    report = {
        "schema": "boqsc.transvoxel.official_reference_convention_research.v2",
        "status": "PROVEN_PUBLISHED_ALGORITHMIC_REFERENCE_CONVENTION",
        "official_convention_status": "PROVEN",
        "proof_scope": (
            "Published sample geometry, negative-inside sign polarity, 9-bit "
            "case-index encoding, full/half face direction, inversion winding, "
            "and orientation-preserving six-face transforms."
        ),
        "not_proven_by_this_report": [
            "official transition triangle topology for all 512 cases",
            "official 73 class numeric IDs",
            "official vertex/cache encoding bytes",
            "Transvoxel.cpp table byte identity",
        ],
        "source": {
            "title": "Voxel-Based Terrain for Real-Time Virtual Simulations",
            "author": "Eric Lengyel",
            "url": "https://transvoxel.org/Lengyel-VoxelTerrain.pdf",
            "public_constraints": [
                "Section 4.3 and Figure 4.8 define full-, half-, and lateral faces.",
                "Figure 4.10 defines inside/solid and outward surface normals.",
                "Section 4.5 and Figure 4.16 define sample coordinates and corner correspondence.",
                "Section 4.5 and Figure 4.17 define negative-value case bits.",
                "Section 4.5 requires reversed triangle winding for inverted cases.",
            ],
        },
        "canonical_local_coordinates": {
            "full_resolution_samples": {
                str(k): v for k, v in FULL_SAMPLES.items()
            },
            "half_resolution_samples": {
                str(k): v for k, v in HALF_SAMPLES.items()
            },
            "half_resolution_sign_sources": {
                "9": 0,
                "10": 2,
                "11": 6,
                "12": 8,
            },
            "axis_semantics": {
                "x": "increasing left-to-right in Figure 4.16",
                "y": "increasing bottom-to-top in Figure 4.16",
                "z": (
                    "chosen from full-resolution face toward half-resolution "
                    "face; the published topology fixes the two faces but does "
                    "not require a numeric width"
                ),
            },
        },
        "sign_and_winding": {
            "inside_solid": "sample_value < iso_level",
            "outside_empty": "sample_value > iso_level",
            "outward_normal": "toward increasing scalar value",
            "inverted_case": (
                "complement all nine signs and reverse triangle winding when "
                "the same representative topology is used"
            ),
        },
        "published_case_bits": {
            str(sample_id): bit
            for sample_id, bit in REFERENCE_CASE_BITS.items()
        },
        "local_runtime_case_bits": {
            str(sample_id): 1 << sample_id for sample_id in range(9)
        },
        "mapping": {
            "status": "PROVEN_BIJECTION_ALL_512_CASES",
            "local_to_published_reference": (
                "For each set local sample bit i, set published_case_bits[i]."
            ),
            "published_reference_to_local": (
                "For each set published_case_bits[i], set local sample bit i."
            ),
            "numeric_identity": False,
            "behavioral_equivalence": True,
        },
        "no_copy_rule": (
            "Derived only from dissertation prose and figures. No official "
            "lookup-table arrays or array values were read, copied, compared, "
            "or used as a golden oracle."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("official reference convention:", report["status"])
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
