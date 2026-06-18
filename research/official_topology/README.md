# Official Topology Research Track

This track exists to study whether a clean-room 0BSD implementation can derive the official Transvoxel-style 73-class transition topology **without copying MIT-licensed table data**.

This is separate from `core/independent/` so the working 0BSD core does not get destabilized while research continues.

Current status:

```text
73-class clean-room research partition: DERIVED
official class ID mapping: NOT_PROVEN
reference_sign_orientation_equivalence: NOT_PROVEN
original_topology_equivalence: NOT_PROVEN
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
