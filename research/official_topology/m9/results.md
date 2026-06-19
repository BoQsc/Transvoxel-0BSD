# M9 M4 Terrain Export Proof

M9 validates the selectable M4 backend through the terrain OBJ export path.

- Status: `PASS_M9_M4_TERRAIN_EXPORT_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M8 status: `PASS_M8_M4_BACKEND_PACKAGE_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Terrain C validation: `PASS_M4_TERRAIN_NORMAL_API_EXPORT`
- Compiler: `zig cc`
- Default core replaced: `False`

## Terrain export comparison

- Default backend: `default_independent`
- M4 backend: `m4_candidate`
- High LOD triangles default/M4: `126` / `126`
- Transition triangles default/M4: `36` / `6`
- Low LOD triangles default/M4: `32` / `32`
- Comparison status: `PASS`

## What passed

- compiled terrain export with the default independent backend;
- compiled terrain export with the optional M4 backend installed;
- both modes wrote OBJ, MTL, and terrain reports;
- regular high-LOD and low-LOD triangle counts stayed unchanged;
- transition-strip triangle count changed only when M4 was installed;
- M4 path uses the normal tv_build_transition_cell terrain call pattern;

## What remains unproven

- Godot runtime terrain export through the M4 backend;
- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- decision to make M4 the default backend.
