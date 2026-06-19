# M9 M4 Terrain Export Proof

M9 validates the selectable M4 candidate backend through a higher-level terrain
LOD export path.

It compiles and runs `examples/c_terrain_export/main.c` twice:

- default independent backend;
- optional M4 backend installed through `transvoxel_m4_backend.h`.

The validation checks that both modes write OBJ/MTL/report files, the high-LOD
and low-LOD regular-cell triangle counts stay unchanged, and only the
transition strip changes when M4 is installed.

This is still not a Godot runtime proof and does not prove official
`Transvoxel.cpp` topology equivalence.

Run:

```text
RUN_M9.cmd
```
