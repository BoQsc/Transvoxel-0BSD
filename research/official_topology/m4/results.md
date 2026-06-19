# M4 Runtime Candidate Tables

M4 converts the M3 clean-room topology derivation into runtime-ready candidate tables.

- Status: `PASS_M4_RUNTIME_TABLES_INTERNAL_CONSTRAINTS_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Runtime table: `generated/official_topology_candidate_tables.json`
- C header: `generated/official_topology_candidate_tables.h`
- Cases: `512`
- Research classes: `73`
- Total runtime vertex pairs: `4096`
- Total runtime triangles: `2640`
- SHA-256: `e1b833af6dbcfb0644fa9913a7104b9e64912807ef5a905cd6e9b96b0b6492b6`
- Zig header smoke: `PASS_ZIG_HEADER_SMOKE`

## What passed

- all 512 cases are present;
- all 73 M3 research classes are present;
- every case has a D4/complement transform from its class representative;
- every generated vertex lies on a sign-changing sample edge;
- every case preserves the M3-derived boundary exactly;
- no generated triangle complex has degenerate triangles, overused edges, or non-adjacent intersections;
- every triangle component has coherent internal edges and deterministic outward winding under the clean-room transition scalar interpolant;
- flat runtime arrays match the per-case records;
- generated JSON and C header regenerate deterministically.

## Zig C header smoke

- Zig compiled and ran a C99 include smoke test for the generated header.

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- official vertex encoding equivalence;
- production replacement status in the default C core.

The generated M4 tables are a candidate replacement path, not the default core table.
