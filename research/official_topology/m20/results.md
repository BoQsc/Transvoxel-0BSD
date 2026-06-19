# M20 Clean-Room Regular-Cell Equivalence

M20 replaces the fixed-diagonal tetrahedral regular table with a preferred-polarity modified-Marching-Cubes derivation compatible with M4.

- Status: `PASS_M20_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE`
- M19 transition topology: `PASS_M19_PUBLISHED_TRANSITION_TOPOLOGY_BEHAVIOR`
- Python regular proof: `PASS_CLEAN_ROOM_REGULAR_CELL_EQUIVALENCE`
- Zig C runtime proof: `PASS_M20_ZIG_CLEAN_ROOM_REGULAR_CELL_RUNTIME`
- Godot regular-table runtime executed: `True`
- Readiness regular gate: `PASS`

## Exhaustive coverage

- Cases / behavior classes: `256` / `18`
- Vertices / triangles: `1536` / `820`
- Maximum vertices / triangles: `12` / `5`
- Regular/regular seam comparisons: `12288`
- Regular/M4 seam comparisons: `40960`
- Failures: `0`

## Readiness effect

- Remaining blocking gates: `6`
- Next milestone: `M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY`

M20 proves functional regular-cell behavior. Exact regular class numbering, reuse encoding, and bytes remain separate compatibility claims.
