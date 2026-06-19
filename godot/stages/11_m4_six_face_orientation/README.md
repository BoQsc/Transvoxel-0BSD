# Stage 11: M4 six-face orientation

This headless Godot stage validates the optional M4 candidate in explicit
right-handed transition frames for `+X`, `-X`, `+Y`, `-Y`, `+Z`, and `-Z`.

For every face it:

- transforms all 512 cases from the local transition-cell frame;
- validates triangle indices, nondegeneracy, transformed winding, and inverse
  frame round trips;
- builds an `ArrayMesh` and reads it with `MeshDataTool`;
- validates deterministic neighboring-cell side seams.

The runtime output is:

```text
godot/validation/11_m4_six_face_orientation/m4_six_face_orientation.json
```

This proves internal six-face runtime consistency. It does not prove that the
frame convention or topology is equivalent to the official `Transvoxel.cpp`.
