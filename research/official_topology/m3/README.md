# Official Topology M3

M3 derives class-level transition-cell triangulation constraints from public geometry and ambiguity rules without reading official Transvoxel table arrays.

Run from the repository root:

```text
RUN_M3.cmd
```

Or:

```text
python research/official_topology/m3/run_m3.py
```

The runner uses only the Python standard library.

## Scope

M3 implements:

- a clean-room `51 + 18 + 4 = 73` research-class partition;
- preferred-polarity contours for the four full-resolution quadrants;
- the same contour rule for the half-resolution face;
- the documented three-sample lateral-face contour configurations;
- closed boundary-loop extraction for all 512 transition cases;
- boundary-only candidate triangulations with no synthetic center vertex;
- a structural comparison with the current independent tetrahedral core.

The numeric research class IDs are locally assigned. They are not claimed to be official class IDs.

## Outputs

```text
class_partition.json
boundary_loops.json
candidate_triangulations.json
independent_core_comparison.json
m3_report.json
results.md
```

## Current result

```text
73 research classes: DERIVED
512 closed boundary-loop cases: PASS
512 candidate triangulations: PASS
official class ID mapping: NOT_PROVEN
official triangle topology equivalence: NOT_PROVEN
official vertex encoding equivalence: NOT_PROVEN
```

Case 341 is the key non-disk case. Its two nested full-resolution contours must be filled as an annulus; filling them as two independent disks creates overlapping geometry.

The current independent core remains the release-candidate implementation. M3 is a separate research construction and does not replace it.

## Public derivation sources

- Eric Lengyel, *Voxel-Based Terrain for Real-Time Virtual Simulations*, Section 3.2 and Section 4.3: https://transvoxel.org/Lengyel-VoxelTerrain.pdf
- Public Transvoxel overview: https://transvoxel.org/

See `CLEAN_ROOM_RULES.md` and `SOURCES.md` at the repository root.
