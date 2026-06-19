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

## M7 result

M7 makes the M4 candidate backend selectable through the normal public
`tv_build_transition_cell()` API. The default backend remains active unless a
project compiles the M4 adapter and installs it explicitly:

```text
include/transvoxel_m4_backend.h
src/transvoxel_m4_backend.c
```

API:

```text
tv_install_m4_transition_backend_candidate()
tv_uninstall_m4_transition_backend_candidate()
```

Current M7 result:

```text
Zig C99 compile/run: PASS
normal API default backend 512-case build: PASS
M4 backend install into normal API: PASS
normal API with M4 installed 512-case build: PASS
normal API with M4 installed strip seam validation: PASS
shared side faces checked: 9408
seam failures: 0
uninstall restores default backend: PASS
default 512-case triangles: 12288
M4 512-case triangles: 2640
M4/default count differences: 510
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced by default: false
```

Run:

```text
RUN_M7.cmd
```

## M8 result

M8 makes the selectable M4 candidate backend a package-validated optional source
path. It adds a public package smoke example:

```text
examples/c_m4_backend_switch/
```

and validates that the core package manifest includes:

```text
include/transvoxel_m4_candidate.h
include/transvoxel_m4_backend.h
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
generated/official_topology_candidate_tables.h
```

Current M8 result:

```text
optional M4 backend package compile/run: PASS
M4 install through normal API: PASS
M4 uninstall restores default backend: PASS
package manifest includes optional M4 path: PASS
release zip rebuilt by M8: false
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced by default: false
```

Run:

```text
RUN_M8.cmd
```

## M9 result

M9 validates the selectable M4 candidate backend through the higher-level C
terrain export path:

```text
examples/c_terrain_export/main.c
```

The validation compiles that same example twice: default backend, then M4
backend installed through `transvoxel_m4_backend.h`. The regular high/low
chunks stay unchanged; the transition strip changes only when M4 is installed.

Current M9 result:

```text
default terrain export: PASS
M4 terrain export through normal API: PASS
high/low regular triangle counts unchanged: PASS
transition strip changed under M4: PASS
default transition triangles: 36
M4 transition triangles: 6
Godot runtime M4 validation: NOT_PROVEN
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced by default: false
```

Run:

```text
RUN_M9.cmd
```

## M10 result

M10 adds the M4 candidate table to the Godot generated-data path and adds a
headless Godot stage:

```text
godot/stages/05_m4_candidate_metrics/DumpM4CandidateMetrics.gd
godot/generated/official_topology_candidate_tables.json
```

The local M10 proof runs the Python-equivalent validator for that stage and
executes the stage when a Godot executable is available:

```text
tools/validate_m4_godot_candidate.py
```

Current M10 result:

```text
M4 table synced into godot/generated: PASS
Godot project preflight includes M4 stage/table: PASS
M4 Godot-style strip builds: 5376
M4 Godot-style shared faces checked: 9408
M4 Godot-style seam failures: 0
M4 invalid triangles: 0
M4 degenerate triangles: 0
actual Godot M4 stage execution: PASS when Godot is available
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced by default: false
```

Run:

```text
RUN_M10.cmd
```

## M11 result

M11 validates a real Godot viewer/export path for the optional M4 candidate:

```text
godot/stages/08_m4_candidate_viewer/DumpM4CandidateViewer.gd
tools/validate_m4_godot_viewer.py
```

The stage loads the synced M4 candidate table, builds `ArrayMesh` objects for a
case gallery and a deterministic terrain-strip-style mesh, and validates
`MeshDataTool` readback.

Current M11 result:

```text
actual Godot M4 viewer/export execution: PASS when Godot is available
case gallery ArrayMesh: PASS
terrain-strip-style ArrayMesh: PASS
MeshDataTool readback: PASS
official Transvoxel.cpp equivalence: NOT_PROVEN
default core replaced by default: false
```

Run:

```text
RUN_M11.cmd
```

## M12 result

M12 validates a Godot default-vs-M4 backend comparison path:

```text
godot/stages/09_m4_backend_compare/DumpM4BackendCompare.gd
tools/validate_m4_godot_backend_compare.py
```

The stage loads both the default independent transition table and the optional
M4 candidate table, builds the same deterministic transition-strip-style mesh
through both paths, and records a side-by-side comparison.

Current M12 result:

```text
actual Godot default-vs-M4 comparison execution: PASS when Godot is available
same case sequence: PASS
default mesh ArrayMesh/MeshDataTool: PASS
M4 mesh ArrayMesh/MeshDataTool: PASS
M4 structurally distinct from default: PASS
default backend by default: true
M4 requires explicit selection: true
official Transvoxel.cpp equivalence: NOT_PROVEN
```

Run:

```text
RUN_M12.cmd
```

## M13 result

M13 validates a scripted-edit comparison path for default-vs-M4 Godot mesh
generation:

```text
godot/stages/10_m4_scripted_edit_compare/DumpM4ScriptedEditCompare.gd
tools/validate_m4_godot_scripted_edit_compare.py
```

The stage runs deterministic dig/add edits over multiple fields and origins,
then builds both explicit backend outputs after every edit.

Current M13 result:

```text
actual Godot scripted edit comparison execution: PASS when Godot is available
scripted edits changed case sequences: PASS
default mesh ArrayMesh/MeshDataTool after edits: PASS
M4 mesh ArrayMesh/MeshDataTool after edits: PASS
M4 structurally distinct from default: PASS
default backend by default: true
M4 requires explicit selection: true
official Transvoxel.cpp equivalence: NOT_PROVEN
```

Run:

```text
RUN_M13.cmd
```

## M14 result

M14 adds an explicit replacement-readiness gate:

```text
tools/m4_replacement_readiness.py
validation/m4_replacement_readiness_report.json
validation/m4_replacement_readiness_report.md
```

The gate distinguishes optional transition-backend readiness from default
replacement, functional full replacement, and exact table compatibility.

Current M14 result:

```text
optional M4 transition backend candidate: READY
replace default transition backend: BLOCKED
functional full Transvoxel.cpp replacement: BLOCKED
exact table/encoding compatibility: BLOCKED
next milestone before M15: M15 M4 six-face orientation validation
```

Run:

```text
RUN_M14.cmd
```

## M15 result

M15 adds an explicit right-handed transition-frame contract and validates M4
through all six axis directions:

```text
include/transvoxel_m4_candidate.h
src/transvoxel_m4_candidate.c
examples/c_m15_m4_six_faces/main.c
godot/stages/11_m4_six_face_orientation/DumpM4SixFaceOrientation.gd
tools/validate_m4_six_face_orientation.py
```

Current M15 result:

```text
Zig C six-face execution: PASS
Godot six-face execution: PASS
all 512 cases per face: PASS
ArrayMesh/MeshDataTool per face: PASS
transformed winding and inverse frame checks: PASS
deterministic neighbor side seams per face: PASS
official reference convention equivalence: NOT_PROVEN
official transition topology equivalence: NOT_PROVEN
next milestone: M16 M4 multi-face corner/junction validation
```

Run:

```text
RUN_M15.cmd
```
