# Official Topology Research Track

This track exists to study whether a clean-room 0BSD implementation can derive the official Transvoxel-style 73-class transition topology **without copying MIT-licensed table data**.

This is separate from `core/independent/` so the working 0BSD core does not get destabilized while research continues.

Current status:

```text
73-class clean-room research partition: DERIVED
official class ID mapping: NOT_PROVEN
published_reference_sign_orientation_equivalence: PROVEN_M18
published_transition_topology_behavior: PROVEN_M19
clean_room_regular_cell_equivalence: PROVEN_M20
exact_official_triangulation_identity: NOT_PROVEN
```

## M3

`m3/` derives boundary contours, closed loops, and candidate triangulations for
all 512 transition cases.

Run:

```text
RUN_M3.cmd
```

Current M3 result:

```text
51 base classes
+18 full-resolution ambiguity inverse classes
+ 4 half-resolution-only ambiguity inverse classes
=73 clean-room research classes

512 boundary-loop cases: PASS
512 candidate triangulations: PASS
official triangulation equivalence: NOT_PROVEN
```

## M4

`m4/` converts the M3 clean-room topology result into runtime-ready candidate
tables without replacing the current default C core.

Run:

```text
RUN_M4.cmd
```

Current M4 result:

```text
512 runtime cases: PASS
73 research classes: PASS
D4/complement reconstruction: PASS
runtime vertex pairs: 4096
runtime triangles: 2640
Zig C header smoke: PASS
official Transvoxel.cpp equivalence: NOT_PROVEN
```

Primary outputs:

```text
generated/official_topology_candidate_tables.json
generated/official_topology_candidate_tables.h
research/official_topology/m4/results.md
```

## M5

`m5/` adds an opt-in C runtime builder for the M4 candidate tables. The default
`tv_build_transition_cell()` backend is unchanged.

Run:

```text
RUN_M5.cmd
```

Current M5 result:

```text
opt-in M4 C builder: PASS
Zig C99 compile/run: PASS
512 transition cases built: PASS
runtime vertex pairs: 4096
runtime triangles: 2640
default core replaced: false
official Transvoxel.cpp equivalence: NOT_PROVEN
```

Primary API:

```text
include/transvoxel_m4_candidate.h
src/transvoxel_m4_candidate.c
tv_m4_build_transition_cell_candidate(...)
```

## M6

`m6/` validates the opt-in M4 C backend across deterministic transition-cell
strips and compares it against the existing default backend.

Run:

```text
RUN_M6.cmd
```

Current M6 result:

```text
Zig C99 compile/run: PASS
M4 strip builds: 5376
shared side faces checked: 9408
seam failures: 0
default backend 512-case build: PASS
M4 backend 512-case build: PASS
M4/default structurally distinct: PASS
default core replaced: false
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M7

`m7/` makes the M4 candidate selectable through the normal
`tv_build_transition_cell()` API using an explicit backend install/uninstall
adapter. The default backend remains active unless the adapter is compiled and
installed.

Run:

```text
RUN_M7.cmd
```

Current M7 result:

```text
normal API default backend 512-case build: PASS
M4 backend install into normal API: PASS
normal API with M4 installed 512-case build: PASS
normal API with M4 installed strip seams: PASS
shared side faces checked: 9408
seam failures: 0
uninstall restores default backend: PASS
default core replaced by default: false
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M8

`m8/` validates the selectable M4 candidate backend as an optional package
source path. It does not rebuild the release zip.

Run:

```text
RUN_M8.cmd
```

Current M8 result:

```text
M7 backend switch proof: PASS
optional M4 backend package example: PASS
package manifest includes optional M4 files: PASS
default core replaced by default: false
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M9

`m9/` validates the selectable M4 candidate backend through the C terrain OBJ
export path. It compiles `examples/c_terrain_export/main.c` once with the
default backend and once with the M4 backend installed.

Run:

```text
RUN_M9.cmd
```

Current M9 result:

```text
default terrain export: PASS
M4 terrain export through normal API: PASS
regular high/low chunk counts unchanged: PASS
transition strip changed under M4: PASS
Godot runtime M4 validation: NOT_PROVEN
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M10

`m10/` validates the M4 candidate table in the Godot generated-data path. It
adds a headless Godot stage, runs the equivalent Python metrics validator, and
executes the Godot stage when Godot is available.

Run:

```text
RUN_M10.cmd
```

Current M10 result:

```text
M4 table synced into godot/generated: PASS
Godot project preflight includes M4 stage/table: PASS
M4 Godot-style seam failures: 0
actual Godot M4 stage execution: PASS when Godot is available
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M11

`m11/` validates the M4 candidate table through a real Godot viewer/export mesh
path. It builds `ArrayMesh` objects from the M4 candidate cases and verifies
`MeshDataTool` readback.

Run:

```text
RUN_M11.cmd
```

Current M11 result:

```text
M4 table available in godot/generated: PASS
Godot ArrayMesh case gallery: PASS
Godot ArrayMesh terrain-strip-style mesh: PASS
MeshDataTool readback: PASS
default core replaced: false
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M12

`m12/` validates an explicit default-vs-M4 Godot backend comparison path. It
builds the same deterministic transition-strip-style mesh with the default
independent transition table and the optional M4 candidate table.

Run:

```text
RUN_M12.cmd
```

Current M12 result:

```text
default Godot transition mesh path: PASS
M4 Godot transition mesh path: PASS
same deterministic case sequence: PASS
M4 output structurally distinct from default: PASS
default backend by default: true
M4 requires explicit selection: true
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M13

`m13/` validates an explicit default-vs-M4 Godot comparison path after
deterministic scripted terrain edits. It runs multiple fields and origins,
applies dig/add edits, and builds both selected transition-strip-style mesh
outputs after every edit.

Run:

```text
RUN_M13.cmd
```

Current M13 result:

```text
default Godot scripted edit mesh path: PASS
M4 Godot scripted edit mesh path: PASS
scripted edits changed case sequences: PASS
M4 output structurally distinct from default: PASS
default backend by default: true
M4 requires explicit selection: true
official Transvoxel.cpp equivalence: NOT_PROVEN
```

## M14

`m14/` converts the accumulated evidence into an explicit machine-readable
replacement-readiness decision.

Run:

```text
RUN_M14.cmd
```

Current M14 result:

```text
optional M4 transition backend candidate: READY
replace default transition backend: BLOCKED
functional full Transvoxel.cpp replacement: BLOCKED
exact table/encoding compatibility: BLOCKED
next milestone before M15: M15 M4 six-face orientation validation
```

## M15

`m15/` adds reusable explicit M4 face frames and validates the candidate in
Zig-compiled C and actual Godot runtime execution for all six axis directions.

Run:

```text
RUN_M15.cmd
```

Current M15 result:

```text
face directions: 6
oriented case builds: 3072
oriented triangles: 15840
shared side faces checked: 4032
invalid/degenerate triangles: 0
frame/transform/winding failures: 0
seam failures: 0
six-face replacement-readiness gate: PASS
official reference/topology equivalence: NOT_PROVEN
next milestone before M16: M16 M4 multi-face corner/junction validation
```

## M16

`m16/` derives non-box transition-cell mapping for block corners from the
public transition-cell geometry and validates three perpendicular M4 cells in
Zig C and actual Godot runtime execution.

Run:

```text
RUN_M16.cmd
```

Current M16 result:

```text
signed corner octants: 8
junction scenarios: 448
mapped transition-cell builds: 1344
shared lateral faces: 1344
shared sample comparisons: 6720
invalid/degenerate triangles: 0
internal/lateral winding failures: 0
lateral geometry failures: 0
corner position/value failures: 0
corner-junction replacement-readiness gate: PASS
official reference/topology equivalence: NOT_PROVEN
next milestone before M17: M17 M4-selected production gate
```

## M17

`m17/` combines normal-API backend selection, mapped corner geometry, terrain
export, Godot scripted edits, six-face/corner evidence, and the base production
gate.

Run:

```text
RUN_M17.cmd
```

Current M17 result:

```text
normal API M4 cases: 512
mapped production builds: 672
normal/mapped C failures: 0
Godot scripted edits: PASS
base production gate: PASS
M4-selected production gate: PASS
ready to replace default transition backend: true
functional full replacement ready: false
official reference/topology equivalence: NOT_PROVEN
next milestone: M18 official reference-convention validation
```

## M18

`m18/` derives the published transition-cell convention from dissertation
Sections 4.3 and 4.5 and Figures 4.8, 4.10, 4.16, and 4.17. It proves the M4
runtime convention through an explicit case-index permutation without reading
official lookup-table arrays.

Run:

```text
RUN_M18.cmd
```

Current M18 result:

```text
published sample/sign/face/winding convention: PROVEN
local/reference case-index bijection: 512/512 PASS
D4 transform/index comparisons: 4096 PASS
same-topology inverse winding pairs: 143/143 PASS
six orientation-preserving face frames: PASS
Zig C conversion API and 512 runtime builds: PASS
official transition topology equivalence: NOT_PROVEN
next milestone: M19 official transition-topology validation
```

## M19

`m19/` validates the public full-, half-, and lateral-face topology rules, the
D4/conditional-inversion behavior classes, and minimal genus-zero candidate
surfaces for all 512 cases.

Run:

```text
RUN_M19.cmd
```

Current M19 result:

```text
public face-rule checks: 4608 PASS
clean-room behavior classes: 73
cases: 512
boundary loops: 730
surface components: 729
candidate triangles: 2640
failures: 0
published transition topology behavior: PROVEN
exact official interior triangulation identity: NOT_PROVEN
next milestone: M20 clean-room regular-cell equivalence
```

## M20

`m20/` replaces the old regular marching-tetrahedra baseline with a clean-room
preferred-polarity modified-Marching-Cubes table and proves its compatibility
with M4.

Run:

```text
RUN_M20.cmd
```

Current M20 result:

```text
cases / behavior classes: 256 / 18
vertices / triangles: 1536 / 820
maximum vertices / triangles: 12 / 5
regular-neighbor comparisons: 12288 PASS
regular/M4 comparisons: 40960 PASS
Zig C runtime: PASS
actual Godot load: PASS
functional regular-cell equivalence: PROVEN
next milestone: M21 consumer compatibility/default selection
```

## M21-M23

M21 selects the clean-room M4 transition table by default and proves the public
C/C++ functional consumer contract. M22 locks the distinction between
functional replacement and exact identity claims. M23 establishes the pinned
external-oracle baseline for all 768 cases.

Run:

```text
RUN_M21.cmd
RUN_M22.cmd
RUN_M23.cmd
```

## M24-M25

M24 selects exact oriented topology from independently enumerated boundary-loop
fillings and matches all 256 regular plus 512 transition cases. M25 compresses
that topology into compatible 16/56 class capacities, derives packed reuse
fields, emits the original data symbols, and passes an unchanged-style C++
consumer.

The M24-M25 exact data remains research-only because the exact filling
selection indexes were calibrated by the MIT oracle.

Run:

```text
RUN_M24.cmd
RUN_M25.cmd
```

## M26

M26 generates the table translation unit expected by the pinned Godot Voxel
consumer and builds the same Godot-style source against both table
implementations with Zig C++.

Current M26 result:

```text
regular records: 256/256
transition records: 512/512
transition corner records: 13/13
mismatches: 0
full Windows GDExtension build with Zig: PASS
exact semantic drop-in integration: READY
exact semantic drop-in 0BSD release: BLOCKED on provenance
next milestone: M27 independent exact-topology provenance
```

Run:

```text
RUN_M26.cmd
```

Allowed:

```text
- derive topology from public papers, diagrams, and first principles
- generate our own signatures and invariants
- compare high-level counts and structural properties
- keep reproducible scripts and notes
```

Not allowed:

```text
- copy official MIT table arrays
- translate official table values into another language
- use official table values as a golden-output oracle
- edit our generated arrays until they match official arrays
```
