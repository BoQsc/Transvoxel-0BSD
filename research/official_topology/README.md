# Official Topology Research Track

This track exists to study whether a clean-room 0BSD implementation can derive the official Transvoxel-style 73-class transition topology **without copying MIT-licensed table data**.

This is separate from `core/independent/` so the working 0BSD core does not get destabilized while research continues.

Current status:

```text
official_73_class_mapping: NOT_PROVEN
reference_sign_orientation_equivalence: NOT_PROVEN
original_topology_equivalence: NOT_PROVEN
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
