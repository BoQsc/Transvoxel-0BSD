# Drop-in use

## Choose the path before embedding

Start with the official upstream MIT `Transvoxel.cpp` behind a stable adapter
for the most conservative production path. Establish a long-term baseline
before considering this 0BSD package. Switch only after the 0BSD backend passes
equivalent visual, collision, LOD, editing, streaming, and performance tests.

The public 0BSD core matches per-case counts, crossing-edge vertex sets, and
tested seam boundaries, but uses different valid interior connectivity in
170/256 regular and 373/512 transition cases. Read
`docs/CHOOSING_0BSD_OR_MIT.md` before selecting it.

After selecting the 0BSD path, use the small release package:

```text
dist/transvoxel_0bsd_core.zip
```

Copy these files into your project:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
```

Compile `src/transvoxel.c` with your project and include both directories:

```sh
-Iinclude -Igenerated
```

## Build examples

Zig:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

Generic C compiler:

```sh
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

Tiny OBJ terrain example:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_terrain_export/main.c -o terrain_export
./terrain_export
```

It writes:

```text
terrain_lod_seam.obj
terrain_lod_seam.mtl
terrain_lod_seam_report.txt
```

## M4 direct API and callback adapter

The normal `tv_build_transition_cell()` path already uses the clean-room M4
published-topology table by default. The package also includes explicit M4
direct/oriented/mapped APIs and a callback adapter. These are useful for
advanced face-frame calls, mapped edge/corner transition cells, and testing the
public callback hook.

Add these files only if you want those explicit APIs or the callback-adapter
example:

```text
include/transvoxel_m4_candidate.h
include/transvoxel_m4_backend.h
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
generated/official_topology_candidate_tables.h
```

Compile:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c src/transvoxel_m4_candidate.c src/transvoxel_m4_backend.c examples/c_m4_backend_switch/main.c -o c_m4_backend_switch
```

Install the adapter explicitly if you want to test or override the callback
route:

```c
#include "transvoxel_m4_backend.h"

tv_install_m4_transition_backend_candidate();
/* Existing tv_build_transition_cell() calls now route through the M4 adapter. */
tv_uninstall_m4_transition_backend_candidate();
```

This adapter uses the same clean-room M4 topology source as the default path.
Official `Transvoxel.cpp` byte/table identity, class IDs, reuse encoding, and
exact triangulation identity are still `NOT_PROVEN`.

Code that directly reads official class IDs, packed reuse fields, or table
layout is not source-compatible with this public API. The repository's
separate exact path supports that integration boundary under MIT.

For an explicitly oriented transition face, call the direct candidate API:

```c
TvBuildInfo info = tv_m4_build_transition_cell_candidate_oriented(
    samples, 0.0f, TV_M4_FACE_POSITIVE_X, origin, scale,
    vertices, TV_M4_TRANSITION_MAX_VERTICES,
    triangles, TV_M4_TRANSITION_MAX_TRIANGLES);
```

The six built-in face frames are validated by `RUN_M15.cmd`.

For edge/corner cells whose half-resolution face must be inset, generate mapped
sample positions with `tv_m4_transition_frame_sample_positions()` and call
`tv_m4_build_transition_cell_candidate_mapped()`. `RUN_M16.cmd` validates this
path where three perpendicular transition faces meet.

The terrain export example can also be compiled with the M4 callback adapter:

```sh
zig cc -std=c99 -Iinclude -Igenerated -DTV_EXAMPLE_USE_M4_BACKEND_CANDIDATE src/transvoxel.c src/transvoxel_m4_candidate.c src/transvoxel_m4_backend.c examples/c_terrain_export/main.c -o terrain_export_m4
./terrain_export_m4
```

## Mental model

The core is deliberately small:

```text
sample scalar values at known local sample positions
compute a case index
use generated tables to create vertices and triangles
append those triangles to your engine mesh
```

You control:

```text
chunk storage
world streaming
SDF/density sampling
vertex deduplication
normals/tangents/materials
GPU upload
collision generation
LOD policy
```

The core only returns mesh triangles for one cell at a time.

## Regular cell

```c
float samples[TV_REGULAR_SAMPLE_COUNT];
for (int i = 0; i < TV_REGULAR_SAMPLE_COUNT; ++i) {
    TvVec3 p = tv_regular_sample_position(i);
    samples[i] = sample_density(p);
}

TvVec3 vertices[TV_REGULAR_MAX_VERTICES];
TvTriangle triangles[TV_REGULAR_MAX_TRIANGLES];

TvBuildInfo info = tv_build_regular_cell(
    samples,
    0.0f,
    tv_vec3(0, 0, 0),
    tv_vec3(1, 1, 1),
    vertices,
    TV_REGULAR_MAX_VERTICES,
    triangles,
    TV_REGULAR_MAX_TRIANGLES);
```

## Transition cell

```c
float samples[TV_TRANSITION_SAMPLE_COUNT];
for (int i = 0; i < TV_TRANSITION_SAMPLE_COUNT; ++i) {
    TvVec3 p = tv_transition_sample_position(i);
    samples[i] = sample_density(p);
}

tv_transition_fill_derived_samples(samples);

TvBuildInfo info = tv_build_transition_cell(
    samples,
    0.0f,
    tv_vec3(0, 0, 0),
    tv_vec3(1, 1, 1),
    vertices,
    TV_TRANSITION_MAX_VERTICES,
    triangles,
    TV_TRANSITION_MAX_TRIANGLES);
```

`tv_transition_fill_derived_samples()` matches the conservative transition
boundary contract used by the proof suite. The default M4 transition path uses
samples `0..12`; sample `13` is kept for ABI compatibility and ignored by the
default backend. If your engine has true coarse samples, you can provide all 14
transition samples yourself.

## Error handling

Every builder returns `TvBuildInfo`:

```c
if (info.result != TV_OK) {
    /* handle TV_ERROR_NULL, TV_ERROR_SMALL_VERTEX_BUFFER, etc. */
}
```

The maximum buffer sizes are fixed constants:

```text
TV_REGULAR_MAX_VERTICES
TV_REGULAR_MAX_TRIANGLES
TV_TRANSITION_MAX_VERTICES
TV_TRANSITION_MAX_TRIANGLES
```

## What not to expect

This core does not automatically provide:

```text
chunk manager
materials
normals
collision
threading
GPU compute
Godot integration
full gameplay terrain system
```

It is meant to be the small table-driven meshing core that those systems call.
