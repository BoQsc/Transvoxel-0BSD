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
