# M6 M4 Candidate Seam Validation

M6 validates the opt-in M4 C backend across assembled transition-cell strips.

It does not replace the default transition backend.

Run:

```text
RUN_M6.cmd
```

The C validation compiles with Zig and checks:

- deterministic transition strips from seven integer fields;
- 12 seeds per field;
- an 8 x 8 transition-cell grid per field/seed;
- shared side-face fingerprints between adjacent M4 candidate cells;
- no invalid M4 triangle indices, degenerate triangles, or overused edges;
- default backend still builds all 512 transition cases;
- M4 candidate remains structurally distinct from the default independent backend.

M6 remains a candidate-backend milestone:

```text
official Transvoxel.cpp byte/table identity: NOT_PROVEN
official class ID mapping: NOT_PROVEN
official triangle topology equivalence: NOT_PROVEN
default core replaced: false
```
