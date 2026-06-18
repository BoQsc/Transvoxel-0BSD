# M7 Normal API Backend Switch

M7 makes the M4 candidate backend selectable through the normal `tv_build_transition_cell()` C API.

- Status: `PASS_M7_NORMAL_API_M4_BACKEND_SWITCH_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- C validation: `PASS_M7_ZIG_NORMAL_API_BACKEND_SWITCH`
- Compiler: `zig cc`

## Backend switch

- Cases checked: `512`
- Default vertices: `10496`
- Default triangles: `12288`
- M4 vertices through normal API: `4096`
- M4 triangles through normal API: `2640`
- Count differences: `510`
- Default restored after uninstall: `1`

## Normal API M4 seam validation

- Strip builds: `5376`
- Shared faces checked: `9408`
- Seam failures: `0`
- Total vertices: `14909`
- Total triangles: `9503`

## What passed

- compiled with Zig C99;
- normal API default backend builds all 512 cases;
- M4 backend installs into normal tv_build_transition_cell API;
- normal API with M4 installed matches M4 generated counts for all 512 cases;
- normal API with M4 installed passes deterministic strip seam validation;
- M4 backend uninstalls and restores default backend totals;
- default backend and M4 backend remain structurally distinct;

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- Godot validation through the selectable M4 backend;
- decision to make M4 the default backend.
