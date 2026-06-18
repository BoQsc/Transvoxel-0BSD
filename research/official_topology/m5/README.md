# M5 Opt-in C Runtime Candidate

M5 integrates the M4 runtime candidate tables into an opt-in C API.

It does not replace the default transition backend.

Run:

```text
RUN_M5.cmd
```

Added files:

```text
include/transvoxel_m4_candidate.h
src/transvoxel_m4_candidate.c
examples/c_m4_candidate/main.c
```

The public opt-in builder is:

```c
TvBuildInfo tv_m4_build_transition_cell_candidate(...);
```

The M5 Zig validation compiles the candidate C source and exhaustively builds
all 512 M4 transition cases. It checks generated counts, vertex-pair sign
crossings, interpolation positions, triangle indices, and small-buffer error
handling.

M5 remains a candidate path:

```text
official Transvoxel.cpp byte/table identity: NOT_PROVEN
official class ID mapping: NOT_PROVEN
official triangle topology equivalence: NOT_PROVEN
default core replaced: false
```
