# Choosing the 0BSD or MIT Path

The production decision is between the official upstream MIT implementation
and this independent 0BSD core. This repository also contains isolated,
generated MIT exact artifacts for proof and integration testing.

## Recommendation

Start production with the official upstream MIT
[`Transvoxel.cpp`](https://github.com/EricLengyel/Transvoxel). Integrate it
behind a stable project-owned adapter and establish long-term terrain,
rendering, collision, editing, LOD, streaming, and performance baselines.

Use the official upstream MIT path when:

- production conservatism is more important than an all-0BSD dependency set;
- an existing consumer expects the original `Transvoxel.cpp` data contract;
- exact official per-case topology and established output compatibility matter;
- preserving the MIT copyright and permission notice is acceptable.

Use the independent 0BSD core when:

- independent 0BSD provenance is a real project requirement;
- the small public C API is a better integration surface than the original
  table ABI;
- the project can perform engine-level visual, collision, LOD, editing, and
  performance qualification.

Keep the 0BSD core available behind the same adapter as an optional comparison
backend. Switch only after it passes the same production acceptance tests
against the established upstream baseline.

The MIT license permits commercial, closed-source, and modified use. Its
practical distribution obligation is to preserve the copyright and permission
notice in copies or substantial portions.

The generated exact MIT integration artifacts in this repository are:

```text
research/official_topology/m25/generated/Transvoxel.cpp
    original-compatible Transvoxel.cpp data surface

research/official_topology/m26/generated/transvoxel_tables.cpp
    pinned Godot Voxel table-source replacement

research/official_topology/MIT_ARTIFACTS.json
    authoritative file list and license boundary
```

The accompanying license is `LICENSES/MIT.txt`.

These files prove compatibility and support controlled integration tests. They
are not the recommended initial production source when the actual official
upstream implementation can be used directly.

## What the 0BSD path matches

For every regular and transition case, the independent core matches the exact
path's:

- vertex count;
- triangle count;
- crossing-edge vertex set;
- tested boundary contour and neighboring-cell seam behavior.

It also has deterministic generation, validated winding, all-six-face
transition orientation tests, corner-junction tests, C and C++ consumer tests,
and Godot validation stages.

## What differs

Exact oriented interior topology matches:

```text
regular cases:    86 / 256
transition cases: 139 / 512
```

Therefore, 170 regular cases and 373 transition cases use a different valid
interior triangulation or diagonal than the MIT exact path. The official
numeric class IDs, compressed table layout, packed bytes, and byte identity
are also not reproduced by the public 0BSD core.

The published Transvoxel rules constrain crack-free boundaries but do not
uniquely choose every authored interior triangulation. The isolated exact path
uses MIT-oracle-calibrated selections and is consequently licensed MIT.

## Long-term engineering tradeoffs

The main expected downside of the 0BSD path is not LOD seam cracking. The
boundary proof specifically targets that risk. The long-term differences are:

- less production history than the original MIT tables;
- different local piecewise-planar surfaces in the cases listed above, which
  can affect generated normals, lighting, interpolation, collision triangles,
  and contact response;
- integration and debugging friction for code written around official class
  IDs, packing, reuse metadata, or table layout;
- project-owned maintenance of the generator, proof gates, and compatibility
  adapters;
- no certification yet for a complete streaming world's visual stability,
  collision behavior, editing behavior, or performance.

The 0BSD core uses direct per-case generated tables behind its own API rather
than exposing the official compressed table ABI. This is simpler for new
callers, but it is not a source-level replacement for code that reads official
tables directly.

## Qualification required for production

Before selecting the 0BSD path for a shipped terrain system, test:

- representative terrain fields and all LOD orientations;
- visual differences under the project's normal and material generation;
- collision meshes and gameplay contact behavior;
- repeated edits, remeshing, and LOD switching;
- chunk boundaries, corner junctions, and streaming transitions;
- memory, build time, and runtime performance at production scale;
- deterministic output across supported compilers and platforms.

Compare against the pinned official upstream backend. Treat any accepted
visual, collision, or performance difference as a project-owned compatibility
decision.

## Bottom line

The 0BSD core is usable and has strong exhaustive case and seam evidence. It
does not have the same topology in every case or the same production history
as the official upstream MIT implementation. Start with upstream MIT, build a
battle-tested baseline, and move to 0BSD only after equivalent real-world
qualification. Choose 0BSD earlier only when its independent provenance is a
hard requirement.
