# Drop-in use

Use the small release zip:

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
terrain_export.obj
```

## Optional M4 candidate backend

The package also includes an opt-in M4 official-topology candidate backend. It
is useful for testing the current 73-class clean-room research path through the
normal public API.

Add these files only if you want that candidate backend:

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

Install it explicitly before building transition cells:

```c
#include "transvoxel_m4_backend.h"

tv_install_m4_transition_backend_candidate();
/* Existing tv_build_transition_cell() calls now use the M4 candidate backend. */
tv_uninstall_m4_transition_backend_candidate();
```

This path remains a candidate. Official `Transvoxel.cpp` byte/table identity and
triangle-topology equivalence are still `NOT_PROVEN`.

The terrain export example can also be compiled with the M4 candidate backend:

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

`tv_transition_fill_derived_samples()` matches the conservative transition boundary contract used by the proof suite. If your engine has true coarse samples, you can provide all 14 transition samples yourself.

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
