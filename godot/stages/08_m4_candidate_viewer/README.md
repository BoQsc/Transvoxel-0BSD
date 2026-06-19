# Stage 08: M4 candidate viewer/export path

This stage loads the optional M4 candidate table from:

```text
res://generated/official_topology_candidate_tables.json
```

and builds real Godot `ArrayMesh` objects from it. The stage writes:

```text
godot/validation/08_m4_candidate_viewer/m4_candidate_viewer.json
```

This is a runtime data-path proof for Godot mesh creation and readback. It does
not make M4 the default backend, and it does not prove official
`Transvoxel.cpp` table or topology equivalence.
