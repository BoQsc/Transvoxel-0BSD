# M11 M4 Godot Viewer/Export Path

M11 validates that the optional M4 candidate table can feed a real Godot mesh
creation path.

It adds:

```text
godot/stages/08_m4_candidate_viewer/DumpM4CandidateViewer.gd
tools/validate_m4_godot_viewer.py
RUN_M11.cmd
```

The Godot stage builds `ArrayMesh` objects for an M4 case gallery and a
deterministic terrain-strip-style mesh, then validates `MeshDataTool` readback.

This is still not official `Transvoxel.cpp` equivalence and it does not make M4
the default backend.
