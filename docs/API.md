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

Use it when you want the included conservative transition boundary contract. Engines with their own true coarse sample source can provide all 14 samples directly.

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

The transition case index uses samples `0..8`. Samples `9..13` are used for interpolation and boundary contract behavior.

## Optional transition backend hook

The default transition builder is the independent backend compiled into
`src/transvoxel.c`. Advanced users can install an alternate transition builder
without changing call sites:

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

The official-topology research track provides an opt-in M4 candidate adapter:

```c
#include "transvoxel_m4_backend.h"

tv_install_m4_transition_backend_candidate();
/* Existing tv_build_transition_cell() calls now use the M4 candidate backend. */
tv_uninstall_m4_transition_backend_candidate();
```

To use that adapter, compile these additional files:

```text
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
generated/official_topology_candidate_tables.h
```

See `examples/c_m4_backend_switch/` for a package-level smoke example.

The M4 backend is still a candidate path. Official `Transvoxel.cpp` equivalence
remains unproven.

## Ownership

The API does not allocate memory. The caller owns all buffers.

## Threading

The builder functions are read-only with respect to generated tables and write only to caller-provided output buffers. They can be called from multiple threads if each call uses separate output buffers.

## Stability goal

For public embedding, prefer treating `include/transvoxel.h` as the stable API surface. The generated table internals may change if a future generator improves compression or topology, but this public builder API should stay small and stable.
