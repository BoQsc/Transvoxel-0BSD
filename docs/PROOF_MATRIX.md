# Proof Matrix

This document separates claims that must not be mixed.

## Claim A - independent 0BSD Transvoxel-style core

The public core solves the practical 2:1 LOD seam problem using independently
generated 0BSD tables and a small C API.

Proven by its gates:

- all 256 regular and 512 transition cases are generated and validated;
- transition boundaries and neighboring transition-cell side faces match;
- generated cases have no duplicate or zero-area triangles;
- winding, six face orientations, and mapped corner junctions are validated;
- Godot seam metrics and scripted edits pass in the documented runtime gates;
- the public C and C++ consumer contracts compile and run;
- vertex count, triangle count, and crossing-edge vertex set match the exact
  path for every case.

The independent path matches exact oriented interior topology in 86/256 regular
and 139/512 transition cases. The other 170 regular and 373 transition cases
use a different valid interior while preserving the tested boundary contract.

## Claim B - exact semantic compatibility

The isolated MIT path proves:

- exact oriented regular topology for 256/256 cases;
- exact oriented transition topology for 512/512 cases;
- compatible original data structures, symbols, capacities, and packed reuse
  semantics;
- 781/781 records through the pinned Godot Voxel table-source API;
- full pinned Windows GDExtension compile/link with Zig.

Still not claimed:

- official numeric class-ID identity;
- byte-for-byte table/source identity;
- 0BSD provenance for the exact oracle-calibrated selection data;
- exhaustive production-world visual, collision, streaming, or performance
  certification.

M27 is terminal: exact semantics are technically proven in the MIT path, while
an exact semantic 0BSD release is `NOT_ACHIEVED`.

## Audit files

The strict functional-core audit writes:

```text
validation/strict_correctness_audit.json
validation/strict_correctness_audit.md
validation/equivalence_class_report.json
validation/winding_normals_report.json
validation/self_intersection_report.json
validation/reference_convention_report.json
validation/corner_junction_report.json
```

Its intentionally narrower status remains:

```text
transvoxel_style_proof: PASS
official_transvoxel_equivalence_proof: NOT_PROVEN
```

That status describes the independent functional proof and does not erase the
later MIT exact evidence or convert it to 0BSD.

## Historical v30 topology-signature result

v30 derived topology signatures without reading external table values:

```text
exact_sample_edge_topology:          256 classes
d4_sample_edge_topology:             201 classes
d4_complement_sample_edge_topology:  201 classes
graph_only_topology_coarse:          484 classes
raw_d4_complement_orbit:              51 classes
official target:                      73 classes
```

This was input to the later M23-M27 investigation, not the final
repository-wide compatibility conclusion.

## Production meaning

Start with the official upstream MIT `Transvoxel.cpp` for production. Keep both
backends behind a stable adapter, build a battle-tested baseline, and switch to
0BSD only after equivalent visual, collision, editing, LOD, streaming, and
performance qualification. See `docs/CHOOSING_0BSD_OR_MIT.md`.
