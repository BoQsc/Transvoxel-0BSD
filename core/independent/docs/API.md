# C API

The public API is in:

```text
include/transvoxel.h
```

Implementation:

```text
src/transvoxel.c
generated/transvoxel_tables.h
```

## Types

```c
typedef struct TvVec3 {
    float x;
    float y;
    float z;
} TvVec3;

typedef struct TvTriangle {
    uint32_t a;
    uint32_t b;
    uint32_t c;
} TvTriangle;

typedef struct TvBuildInfo {
    int result;
    int case_index;
    int vertex_count;
    int triangle_count;
} TvBuildInfo;
```

## Result codes

```c
TV_OK
TV_ERROR_NULL
TV_ERROR_SMALL_VERTEX_BUFFER
TV_ERROR_SMALL_TRIANGLE_BUFFER
TV_ERROR_BAD_CASE
```

## Buffer limits

```c
TV_REGULAR_SAMPLE_COUNT              /* 8  */
TV_TRANSITION_HIGH_SAMPLE_COUNT      /* 9  */
TV_TRANSITION_SAMPLE_COUNT           /* 14 */

TV_REGULAR_MAX_VERTICES
TV_REGULAR_MAX_TRIANGLES
TV_TRANSITION_MAX_VERTICES
TV_TRANSITION_MAX_TRIANGLES
```

Use these constants for stack arrays or fixed scratch buffers.

The M20 clean-room regular table has exact maxima of 12 vertices and 5
triangles. Its topology is derived from the public preferred-polarity face
rule, not marching tetrahedra.

The M21 clean-room default transition table has exact maxima of 12 vertices
and 12 triangles. It is exported from the M4 published-topology table, not from
the older independent tetrahedral transition generator.

## Utility

```c
TvVec3 tv_vec3(float x, float y, float z);
```

## Sampling positions

```c
TvVec3 tv_regular_sample_position(int sample_id);
TvVec3 tv_transition_sample_position(int sample_id);
```

These return the local sample positions used by the generated tables. Your engine samples its scalar field at those positions, transformed into your chunk/world space.

## Case indices

```c
int tv_regular_case_index(const float samples[TV_REGULAR_SAMPLE_COUNT], float iso_level);
int tv_transition_case_index(const float samples[TV_TRANSITION_SAMPLE_COUNT], float iso_level);
```

A sample is considered inside when:

```text
sample < iso_level
```

## Transition helper

```c
void tv_transition_fill_derived_samples(float samples[TV_TRANSITION_SAMPLE_COUNT]);
```

This fills samples `9..13` from the high-resolution transition face using the same documented source rules as the proof suite:

```text
9  <- 0
10 <- 2
11 <- 6
12 <- 8
13 <- 4
```

Use it when you want the included conservative transition boundary contract.
Engines with their own true coarse sample source can provide all 14 samples
directly. The M21 default M4 transition backend uses samples `0..12`; sample
`13` is retained for public ABI compatibility and ignored by the default path.

## Build regular cell

```c
TvBuildInfo tv_build_regular_cell(
    const float sample_values[TV_REGULAR_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);
```

The output positions are:

```text
origin + local_position * scale
```

The regular builder uses Figure 3.8 corner numbering, `sample < iso_level` as
inside, and a preferred-polarity modified-Marching-Cubes topology. M20 proves
all 256 cases, 18 rotation/inversion behavior classes, same-resolution neighbor
faces, and compatibility with M4 transition full/half faces.

## Build transition cell

```c
TvBuildInfo tv_build_transition_cell(
    const float sample_values[TV_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);
```

The transition case index uses samples `0..8`. The default clean-room M4
transition backend uses samples `9..12` for interpolation and ignores sample
`13`.

## Optional transition backend hook

The default transition builder is the clean-room M4 published-topology backend
compiled into `src/transvoxel.c` through `generated/transvoxel_tables.h`.
Advanced users can install an alternate transition builder without changing
call sites:

```c
typedef TvBuildInfo (*TvTransitionBuilderFn)(
    const float sample_values[TV_TRANSITION_SAMPLE_COUNT],
    float iso_level,
    TvVec3 origin,
    TvVec3 scale,
    TvVec3 *out_vertices,
    int max_vertices,
    TvTriangle *out_triangles,
    int max_triangles);

int tv_set_transition_backend_callback(TvTransitionBuilderFn builder);
TvTransitionBuilderFn tv_get_transition_backend_callback(void);
void tv_reset_transition_backend_callback(void);
int tv_transition_backend_is_custom(void);
```

Passing `NULL` or calling `tv_reset_transition_backend_callback()` restores the
default backend.

The package also provides an explicit M4 callback adapter:

```c
#include "transvoxel_m4_backend.h"

tv_install_m4_transition_backend_candidate();
/* Existing tv_build_transition_cell() calls now route through the M4 adapter. */
tv_uninstall_m4_transition_backend_candidate();
```

Since the default backend already uses the same clean-room M4 topology source,
this adapter is mainly a callback/customization compatibility shim and package
smoke test. To use it, compile these additional files:

```text
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
generated/official_topology_candidate_tables.h
```

See `examples/c_m4_backend_switch/` for a package-level smoke example.

The direct M4 API keeps its generated table in stable row-major sample-bit
order and exposes exact conversion helpers for the published dissertation
Figure 4.17 case index:

```c
int local_case = tv_m4_transition_case_index(samples, iso_level);
int published_case =
    tv_m4_transition_reference_case_index(samples, iso_level);

published_case =
    tv_m4_transition_reference_case_from_local(local_case);
local_case =
    tv_m4_transition_local_case_from_reference(published_case);
```

M18 proves both conversions are bijective across all 512 cases. `TvBuildInfo`
continues to report the stable local runtime-table index.

The direct M4 API also exposes explicit right-handed face frames:

```c
#include "transvoxel_m4_candidate.h"

TvBuildInfo info = tv_m4_build_transition_cell_candidate_oriented(
    samples,
    0.0f,
    TV_M4_FACE_NEGATIVE_Z,
    origin,
    tv_vec3(1.0f, 1.0f, 1.0f),
    vertices,
    TV_M4_TRANSITION_MAX_VERTICES,
    triangles,
    TV_M4_TRANSITION_MAX_TRIANGLES);
```

`TV_M4_FACE_POSITIVE_X` through `TV_M4_FACE_NEGATIVE_Z` name the world
direction of local `+w`. Local `u/v` span the full-resolution face, `+w`
points toward the half-resolution samples and into the low-resolution block,
and `-w` points toward the high-resolution neighbor. M15 validates every case
and neighbor seam in all six frames; M18 proves this is an
orientation-preserving transform of the published canonical cell.

At block edges and corners, transition cells are not rectangular boxes. Build
the 13 mapped sample positions and use:

```c
TvM4TransitionFrame frame = {origin, axis_u, axis_v, axis_w};
TvVec3 mapped[TV_M4_TRANSITION_SAMPLE_COUNT];

tv_m4_transition_frame_sample_positions(
    &frame,
    TV_M4_BOUNDARY_U_MIN | TV_M4_BOUNDARY_V_MIN,
    0.5f,
    0.5f,
    mapped);

TvBuildInfo info = tv_m4_build_transition_cell_candidate_mapped(
    samples, mapped, 0.0f,
    vertices, TV_M4_TRANSITION_MAX_VERTICES,
    triangles, TV_M4_TRANSITION_MAX_TRIANGLES);
```

The mapped builder derives handedness from sample positions and corrects
winding. M16 validates three perpendicular mapped transition cells across all
eight signed corner octants.

M21 proves the functional public C/C++ consumer contract for the clean-room
default regular and transition builders. Exact official table layout, 73-class
IDs, vertex/reuse encoding, triangulation identity, and byte identity remain
separate unproven compatibility claims. M22 locks that claim boundary in
`docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md`.

## Ownership

The API does not allocate memory. The caller owns all buffers.

## Threading

The builder functions are read-only with respect to generated tables and write only to caller-provided output buffers. They can be called from multiple threads if each call uses separate output buffers.

## Stability goal

For public embedding, prefer treating `include/transvoxel.h` as the stable API surface. The generated table internals may change if a future generator improves compression or topology, but this public builder API should stay small and stable.
