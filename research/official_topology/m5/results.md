# M5 Opt-in C Runtime Candidate

M5 adds an opt-in C builder for the M4 runtime candidate topology tables.

- Status: `PASS_M5_OPT_IN_C_RUNTIME_CANDIDATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- C validation: `PASS_M5_ZIG_CANDIDATE_BUILDER`
- Compiler: `zig cc`

## Added runtime path

- `include/transvoxel_m4_candidate.h`
- `src/transvoxel_m4_candidate.c`
- `examples/c_m4_candidate/main.c`

The default `tv_build_transition_cell()` path is unchanged. Engines must opt into M5 with `tv_m4_build_transition_cell_candidate()`.

## Zig validation

- compiled with Zig C99;
- built all 512 M4 transition cases;
- matched generated per-case vertex and triangle counts;
- verified generated vertex pairs cross signs;
- verified emitted vertex interpolation positions;
- verified emitted triangle indices and table copies;
- verified small vertex/triangle buffer error handling;

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- Godot/runtime seam validation through the M4 candidate backend;
- decision to replace the default transition backend.
