# Official Topology Research Track

This track is separate from `core/independent/`. Its purpose is to research whether a no-copy implementation can derive the official-style Transvoxel transition topology and 73 equivalence classes from public algorithm descriptions and first principles.

## Boundary

Allowed:

- use public papers, dissertation text, diagrams, and high-level descriptions;
- derive symmetry groups, topology signatures, orientation frames, and candidate class systems independently;
- compare counts and structural invariants;
- run our own proof gate on any candidate.

Not allowed:

- copy or transcribe MIT table arrays;
- use official table values as golden output;
- tune generated arrays until they match official arrays;
- claim official equivalence before a no-copy derivation exists.

## v32 result

v32 adds a candidate 73-class derivation search, a reference convention matrix, and a public-constraint checker. The current result remains:

```text
independent_core: PASS
official_topology_research: IN_PROGRESS
official_equivalence: NOT_PROVEN
```

The most important diagnostic is that a raw C4+complement sign-pattern model gives 70 classes. Reaching the public target of 73 would require principled splitting of three orbits or a different topology-level equivalence definition.

## M3 result

M3 replaces that early C4 diagnostic with the public D4 ambiguity rule:

```text
51 base D4 classes
+18 inverse classes split by full-resolution ambiguity
+ 4 inverse classes split by half-resolution-only ambiguity
=73 clean-room research classes
```

It derives closed boundary loops and validated candidate triangulations for all
512 cases. The current independent tetrahedral core is structurally distinct,
especially in ambiguity-bearing cases.

This still does not prove official class IDs, official triangle choices,
official vertex encodings, winding compatibility, or table identity.

Run the separate milestone with:

```text
RUN_M3.cmd
```

## M4 result

M4 converts the M3 clean-room topology result into runtime-ready candidate
tables:

```text
generated/official_topology_candidate_tables.json
generated/official_topology_candidate_tables.h
```

The generated candidate table has 512 transition cases, 73 M3 research classes,
D4/complement transform metadata, flat C-friendly arrays, 4096 runtime vertex
pairs, and 2640 runtime triangles.

The M4 validator proves internal constraints only:

```text
512 runtime cases: PASS
73 research classes: PASS
D4/complement reconstruction: PASS
boundary preservation: PASS
flat runtime arrays: PASS
deterministic regeneration: PASS
Zig C header smoke: PASS
official Transvoxel.cpp equivalence: NOT_PROVEN
```

Run:

```text
RUN_M4.cmd
```

The current default C core is not silently replaced by M4. M4 is the candidate
replacement path that later milestones must integrate and test more strictly.

## M5 result

M5 integrates the M4 candidate tables into an opt-in C runtime builder:

```text
include/transvoxel_m4_candidate.h
src/transvoxel_m4_candidate.c
examples/c_m4_candidate/main.c
```

The default `tv_build_transition_cell()` path is unchanged. Engines must opt in
with:

```text
tv_m4_build_transition_cell_candidate(...)
```

The M5 Zig validation compiles and runs the opt-in C path and exhaustively
builds all 512 transition cases:

```text
Zig C99 compile/run: PASS
512 M4 transition cases built: PASS
per-case vertex/triangle counts: PASS
vertex-pair sign crossings: PASS
interpolation positions: PASS
triangle indices/table copies: PASS
small-buffer errors: PASS
runtime vertex pairs: 4096
runtime triangles: 2640
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced: false
```

Run:

```text
RUN_M5.cmd
```

## M6 result

M6 validates the opt-in M4 C backend across assembled transition-cell strips.
It compiles with Zig and runs:

```text
examples/c_m6_m4_seams/main.c
```

The validation uses seven deterministic integer fields, twelve seeds per field,
and an 8 x 8 transition-cell grid per field/seed.

Current M6 result:

```text
Zig C99 compile/run: PASS
M4 strip builds: 5376
shared side faces checked: 9408
seam failures: 0
M4 strip vertices: 14909
M4 strip triangles: 9503
default backend 512-case build failures: 0
M4 backend 512-case build failures: 0
default 512-case triangles: 12288
M4 512-case triangles: 2640
M4/default count differences: 510
M4/default structurally distinct: PASS
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced: false
```

Run:

```text
RUN_M6.cmd
```
