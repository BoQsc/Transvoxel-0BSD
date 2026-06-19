# M10 M4 Godot Data-Path Metrics

M10 validates the M4 candidate table in the Godot generated-data path.

- Status: `PASS_M10_M4_GODOT_DATA_PATH_METRICS_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M9 status: `PASS_M9_M4_TERRAIN_EXPORT_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Godot project preflight: `PASS`
- M4 Godot-style validation: `PASS_M4_GODOT_STYLE_CANDIDATE_METRICS`
- Godot runtime executed: `True`
- Godot M4 stage status: `PASS`

## M4 Godot-style metrics

- Table synced to Godot: `True`
- Cases: `512`
- Samples: `13`
- Strip builds: `5376`
- Shared faces checked: `9408`
- Seam failures / open edges: `0`
- Invalid triangles: `0`
- Degenerate triangles: `0`
- Total M4 triangles: `2640`

## What passed

- M4 table is synced into `godot/generated/`;
- Godot project preflight includes the M4 generated table and stage;
- M4 candidate table satisfies the Godot-style non-visual seam metric contract;
- deterministic M4 strip fingerprints have zero shared-face mismatches;
- M4 triangles are index-valid and non-degenerate under midpoint validation;

## What remains unproven

- Godot viewer/interactive terrain rendering through M4;
- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- decision to make M4 the default backend.
