# Official Topology M3 Results

Status: **PASS_M3_CONSTRAINT_DERIVATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN**

## Result

- The clean-room class partition reproduces `51 + 18 + 4 = 73` research classes.
- Boundary contours form closed degree-2 loops for all 512 cases.
- Boundary-only candidate surfaces validate for all 512 cases with 2640 triangles in total.
- Case 341 contains nested full-resolution contours and is derived as a planar annulus instead of two overlapping disks.
- The current independent core matches M3 anchor connectivity in 374 cases and differs in 138 ambiguity-bearing cases.

## What this means

M3 demonstrates that a complete 512-case boundary contract and a valid candidate surface family can be generated from public geometry and ambiguity rules without reading official table arrays.

It does not prove official triangle choices, official class IDs, official vertex encodings, winding compatibility, or table identity.

## Decision

The M3 topology is structurally different from the current independent tetrahedral core. Further official-style work should remain a separate candidate core rather than replacing the release-candidate core.

## Next milestone

M4 should derive orientation-preserving class transforms and build a separate official-style candidate table from these constraints.
