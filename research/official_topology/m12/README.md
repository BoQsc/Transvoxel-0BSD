# M12 M4 Godot Backend Comparison

M12 validates that Godot can explicitly select and compare the default
independent transition table and the optional M4 candidate table.

It adds:

```text
godot/stages/09_m4_backend_compare/DumpM4BackendCompare.gd
tools/validate_m4_godot_backend_compare.py
RUN_M12.cmd
```

The stage builds the same deterministic transition-strip-style mesh through
both table paths and reports the two valid `ArrayMesh`/`MeshDataTool` outputs.

M4 remains opt-in. This does not prove official `Transvoxel.cpp` equivalence and
does not make M4 the default backend.
