# M4 Runtime Table Schema

Schema:

```text
boqsc.transvoxel.official_topology.m4.runtime_candidate.v1
```

Primary generated files:

```text
generated/official_topology_candidate_tables.json
generated/official_topology_candidate_tables.h
```

Important fields:

- `samples`: sample ids `0..12`; ids `0..8` are full-resolution face samples and ids `9..12` are half-resolution face samples whose signs derive from full-resolution corners.
- `classes`: 73 M3 research classes. Each class stores a representative case, representative vertices, and representative triangles.
- `cases`: 512 runtime case records. Each case stores its research class id, D4/complement transform from the class representative, runtime vertices, and runtime triangles.
- `flat`: C-friendly arrays for case lookup, vertex-pair lookup, triangle lookup, D4 transform metadata, complement metadata, and orientation-flip metadata.

Vertex encoding:

```text
[sample_a, sample_b]
```

The runtime vertex is the interpolated isosurface crossing on that sample edge.

Triangle encoding:

```text
[local_vertex_id_0, local_vertex_id_1, local_vertex_id_2]
```

Triangle ids are local to the case. In the flat arrays, each case uses:

```text
case_vertex_start[case] .. case_vertex_start[case] + case_vertex_count[case]
case_triangle_start[case] .. case_triangle_start[case] + case_triangle_count[case]
```

Triangle components are oriented coherently across shared internal edges, then
oriented toward increasing scalar values using the gradient of the clean-room
piecewise transition interpolant. This winding rule is independently derived;
it is not an official winding-equivalence claim.

Official-equivalence fields must remain:

```text
official_transvoxel_cpp_byte_identity: NOT_PROVEN
official_class_id_mapping: NOT_PROVEN
official_triangle_topology_equivalence: NOT_PROVEN
```
