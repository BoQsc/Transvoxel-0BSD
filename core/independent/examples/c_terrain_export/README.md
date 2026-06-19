# C terrain export example

This example is a small engine-independent demonstration of the public C API.
It writes an OBJ scene with three named parts:

```text
high_lod0_regular_cells                 regular cells, scale 1
transition_strip_between_lod0_and_lod1  transition cells
low_lod1_regular_cells_scale_2          regular cells, scale 2
```

Build with Zig:

```sh
zig cc -std=c99 -I../../include -I../../generated ../../src/transvoxel.c main.c -o terrain_export
```

Build with a normal C compiler:

```sh
cc -std=c99 -I../../include -I../../generated ../../src/transvoxel.c main.c -o terrain_export
```

Build the same terrain example with the explicit M4 callback adapter:

```sh
zig cc -std=c99 -I../../include -I../../generated -DTV_EXAMPLE_USE_M4_BACKEND_CANDIDATE ../../src/transvoxel.c ../../src/transvoxel_m4_candidate.c ../../src/transvoxel_m4_backend.c main.c -o terrain_export_m4
```

Run:

```sh
./terrain_export
```

It writes:

```text
terrain_lod_seam.obj
terrain_lod_seam.mtl
terrain_lod_seam_report.txt
```

Open the OBJ in Blender, MeshLab, Godot, or another viewer. The materials are:

```text
green   high LOD regular cells
orange  transition strip
blue    low LOD regular cells
```

This is not a full streaming terrain engine. It is a readable example showing
how to call the regular-cell and transition-cell builders from plain C.

Default mode and adapter mode should produce the same transition triangle count
after M21, because the default transition path already uses the clean-room M4
published-topology table. Exact official `Transvoxel.cpp` table identity remains
unclaimed.
