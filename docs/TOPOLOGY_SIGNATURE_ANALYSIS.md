# Topology Signature Analysis

This document describes the v30 official-equivalence research step.

The goal is to ask a stricter question than the earlier v29 raw bit-orbit test:

> If we derive topology signatures from our generated transition cases, do those
> signatures naturally collapse toward the public Transvoxel target of 73
> transition-cell equivalence classes?

The answer in v30 is **no**.

## No-copy rule

The analysis uses only:

- `generated/transition_tables.json` from this 0BSD project.
- The public structural fact that the official Transvoxel transition table has
  512 cases and 73 equivalence classes.
- Our own generated sample-edge/triangle data.

It does **not** read, compare, transcribe, or use Eric Lengyel's MIT-licensed
`Transvoxel.cpp` table values.

## Signature families

`tools/topology_signature_analysis.py` computes several class counts:

- `exact_sample_edge_topology`: triangles expressed as interpolated sample-edge
  references, with no symmetry reduction.
- `d4_sample_edge_topology`: sample-edge topology canonicalized by the square
  face's rotations/reflections.
- `d4_complement_sample_edge_topology`: same as above, also allowing inside / outside
  complement.
- `graph_only_topology_coarse`: a coarse unlabeled triangle-incidence signature.
- `raw_d4_complement_orbit`: the older raw 3×3 sign-pattern orbit count, kept as
  a baseline.

## v30 result

The generated v30 report found:

```text
exact_sample_edge_topology:          256 classes
d4_sample_edge_topology:             201 classes
d4_complement_sample_edge_topology:  201 classes
graph_only_topology_coarse:          484 classes
raw_d4_complement_orbit:              51 classes
official target:                      73 classes
```

The closest count to 73 was the raw D4+complement orbit count of 51, still 22
away from the official target.

## Meaning

This is useful evidence, but it is a negative result for official equivalence:

```text
Functional Transvoxel-style seam proof: PASS.
Official 73-class topology equivalence: NOT_PROVEN.
```

It suggests that the current tetrahedralized transition-cell generator is
structurally different from the official 73-class table design, or that the
official classes depend on a richer topology-class relation that is not captured
by these no-copy signatures.

Even if a future no-copy signature count equals 73, that would still not prove
matching official class IDs, table bytes, packed encodings, or triangle order.
It would only be evidence that the generated topology class structure is closer
to the official public description.

## Consequence for the project

The project should continue to make this claim:

> Independent 0BSD Transvoxel-style voxel LOD transition core with strong
> generated-table, C-core, Godot seam, and scripted auto-interaction proof.

It should not claim:

> Public-domain replacement for Eric Lengyel's MIT `Transvoxel.cpp` tables with
> proven official 73-class equivalence.
