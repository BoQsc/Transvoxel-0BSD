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
