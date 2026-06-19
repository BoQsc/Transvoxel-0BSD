# M8 M4 Backend Package Proof

M8 validates the selectable M4 backend as an optional package source path.
It does not rebuild the release zip.

- Status: `PASS_M8_M4_BACKEND_PACKAGE_PROOF_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M7 status: `PASS_M7_NORMAL_API_M4_BACKEND_SWITCH_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Package C validation: `PASS_M4_BACKEND_PACKAGE_C_EXAMPLE`
- Compiler: `zig cc`
- Package manifest: `PASS`
- Zip rebuilt in M8: `False`

## Package C smoke

- Case: `341`
- Default vertices: `24`
- Default triangles: `24`
- M4 vertices: `12`
- M4 triangles: `12`
- Default restored: `1`
- Custom backend after uninstall: `0`

## Package manifest files checked

- `include/transvoxel.h`
- `include/transvoxel_m4_candidate.h`
- `include/transvoxel_m4_backend.h`
- `src/transvoxel.c`
- `src/transvoxel_m4_candidate.c`
- `src/transvoxel_m4_backend.c`
- `generated/transvoxel_tables.h`
- `generated/official_topology_candidate_tables.h`
- `examples/c_m4_backend_switch/main.c`
- `examples/c_m4_backend_switch/BUILD_WITH_ZIG.cmd`
- `examples/c_m4_backend_switch/BUILD_WITH_CC.sh`

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- decision to make M4 the default backend.
