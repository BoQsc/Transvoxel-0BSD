# M6 M4 Candidate Seam Validation

M6 validates the opt-in M4 C backend across deterministic transition-cell strips.

- Status: `PASS_M6_M4_C_SEAM_VALIDATION_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- C validation: `PASS_M6_ZIG_M4_SEAM_VALIDATION`
- Compiler: `zig cc`
- Strip fields: `7`
- Seeds per field: `12`
- Grid size: `8 x 8`
- M4 strip builds: `5376`
- Shared faces checked: `9408`
- Seam failures: `0`
- M4 strip triangles: `9503`

## Default backend comparison

- Cases checked: `512`
- Default build failures: `0`
- M4 build failures: `0`
- Count differences: `510`
- Default triangles: `12288`
- M4 triangles: `2640`
- Structurally distinct: `1`

## What passed

- compiled with Zig C99;
- built M4 candidate transition cells across deterministic strips;
- compared shared side-face fingerprints;
- verified zero strip seam mismatches;
- built default transition backend for all 512 cases;
- confirmed M4 candidate is structurally distinct from default backend;

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- Godot validation through the M4 candidate backend;
- decision to replace the default transition backend.
