# Core Package Contents

The small public package is:

```text
dist/transvoxel_0bsd_core.zip
```

It contains only embedding-oriented files:

```text
include/transvoxel.h              public C API
src/transvoxel.c                  implementation
generated/transvoxel_tables.h     generated tables
include/transvoxel_m4_candidate.h optional M4 candidate direct API
include/transvoxel_m4_backend.h   optional M4 candidate backend adapter
src/transvoxel_m4_candidate.c     optional M4 candidate implementation
src/transvoxel_m4_backend.c       optional adapter for tv_build_transition_cell()
generated/official_topology_candidate_tables.h
                                   optional M4 candidate topology tables
examples/c_minimal/               smallest compile/run example
examples/c_terrain_export/        writes a chunk + LOD seam OBJ example
examples/c_m4_backend_switch/     optional M4 backend install example
docs/API.md                       API reference
docs/DROP_IN.md                   how to embed
docs/WHAT_THIS_PROVES.md          proof boundary
docs/C_COMPILER.md                C compiler notes
docs/KNOWN_LIMITS.md              known limits and non-claims
docs/TESTING_BY_USERS.md          third-party testing and report guide
LICENSE                           0BSD license
PROVENANCE.md                     clean-room provenance
SOURCES.md                        public sources used
README_CORE.txt                   short entry point
```

The M4 files are optional and remain on the official-topology candidate track.
They are not the default backend and do not prove official `Transvoxel.cpp`
equivalence.

The package intentionally excludes Godot, proof outputs, generated JSON, and
official-topology research scripts.
