# Proof Matrix

This document separates two claims that must not be mixed.

## Claim A — independent 0BSD Transvoxel-style core

This project is intended to solve the same practical LOD seam problem using an independently generated 0BSD table/core package.

Current proof target:

- all 512 transition cases are generated and validated against this project's own transition-cell boundary contract;
- transition side faces match neighboring transition cells;
- generated cases have no duplicate triangles or zero-area triangles;
- generated cases pass a conservative midpoint self-intersection audit;
- complement cases expose the same geometry with opposite normals;
- Godot seam metrics and automated scripted edits pass when run locally;
- the public C core compiles and runs when a C compiler is available.

## Claim B — exact original Transvoxel equivalence

This is a stronger claim and is **not proven**.

Not proven yet:

- exact official 73 transition equivalence class mapping;
- byte/table identity with Eric Lengyel's MIT `Transvoxel.cpp`;
- exact same packed table layout and class IDs;
- exact same reference sign convention and sample orientation;
- exact same triangulation topology for every case;
- exhaustive proof for every possible production corner/multi-neighbor streaming junction.

## Audit files

The strict audit writes:

```text
validation/strict_correctness_audit.json
validation/strict_correctness_audit.md
validation/equivalence_class_report.json
validation/winding_normals_report.json
validation/self_intersection_report.json
validation/reference_convention_report.json
validation/corner_junction_report.json
```

The intended honest status is:

```text
transvoxel_style_proof: PASS
official_transvoxel_equivalence_proof: NOT_PROVEN
```

That is not a failure of the 0BSD core. It is a limit on the claim we are allowed to make.

## v26 audit timing note

`RUN_FULL.cmd` reruns the strict correctness audit after Godot seam metrics and auto-interaction are produced. This keeps the uploaded `SEND_TO_CHATGPT.zip` from carrying stale corner-junction status from the earlier Python-only proof phase.

## v30 topology-signature research

v30 adds `tools/topology_signature_analysis.py`, which derives topology
signatures from the generated transition cases without reading external table
values.

Current v30 result:

```text
exact_sample_edge_topology:          256 classes
d4_sample_edge_topology:             201 classes
d4_complement_sample_edge_topology:  201 classes
graph_only_topology_coarse:          484 classes
raw_d4_complement_orbit:              51 classes
official target:                      73 classes
```

This means the project still reports:

```text
transvoxel_style_proof: PASS
official_transvoxel_equivalence_proof: NOT_PROVEN
```
