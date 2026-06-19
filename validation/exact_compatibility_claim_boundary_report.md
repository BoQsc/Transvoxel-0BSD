# M22 Exact Compatibility Claim Boundary

Status: `PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY`

## Allowed public claim

Functional clean-room Transvoxel.cpp replacement through the public C/C++ API: default regular and transition builders use clean-room published behavior; C and C++ consumers can compile/link; callback customization is retained.

## Not allowed without future exact evidence

- Exact official Transvoxel.cpp table layout claim.
- Official 73-class ID compatibility claim.
- Official vertex/reuse encoding compatibility claim.
- Exact official transition triangulation identity claim.
- Exact official regular table identity claim.
- Byte-for-byte Transvoxel.cpp table/file identity claim.

## Evidence

- Readiness: `READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_EXACT_COMPATIBILITY_BLOCKED`
- M21: `PASS_M21_DEFAULT_M4_FUNCTIONAL_CONSUMER_COMPATIBILITY`
- Consumer contract: `PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY`
- Default transition source: `generated/official_topology_candidate_tables.json`
- Default transition totals: `4096` vertex refs / `2640` triangles
