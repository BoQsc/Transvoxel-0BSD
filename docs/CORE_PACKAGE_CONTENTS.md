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
include/transvoxel_m4_candidate.h explicit M4 direct/oriented/mapped API
include/transvoxel_m4_backend.h   M4 callback-adapter API
src/transvoxel_m4_candidate.c     explicit M4 implementation
src/transvoxel_m4_backend.c       callback adapter for tv_build_transition_cell()
generated/official_topology_candidate_tables.h
                                   explicit M4 topology tables
examples/c_minimal/               smallest compile/run example
examples/c_terrain_export/        writes a chunk + LOD seam OBJ example
examples/c_m4_backend_switch/     M4 callback-adapter install example
examples/c_m21_consumer_contract/ exhaustive C consumer contract example
examples/cpp_consumer/            C++ include/link smoke example
docs/API.md                       API reference
docs/DROP_IN.md                   how to embed
docs/CHOOSING_0BSD_OR_MIT.md      production path decision guide
docs/WHAT_THIS_PROVES.md          proof boundary
docs/C_COMPILER.md                C compiler notes
docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md
                                  M22 exact-compatibility claim boundary
docs/KNOWN_LIMITS.md              known limits and non-claims
docs/TESTING_BY_USERS.md          third-party testing and report guide
LICENSE                           0BSD license
LICENSE_SCOPE.md                  confirms this package excludes MIT exact data
PROVENANCE.md                     clean-room provenance
SOURCES.md                        public sources used
README_CORE.txt                   short entry point
```

The default `tv_build_transition_cell()` path is already exported from the
clean-room M4 published-topology source in `generated/transvoxel_tables.h`. The
separate M4 files are included for explicit direct/oriented/mapped APIs and for
the callback-adapter compatibility example. They do not prove exact official
`Transvoxel.cpp` table layout or byte identity.

This package is a functional 0BSD path, not the MIT exact-output path. It uses
different valid interior connectivity in 170/256 regular and 373/512
transition cases. Read `docs/CHOOSING_0BSD_OR_MIT.md` before selecting it for a
production terrain system.

The package intentionally excludes Godot, proof outputs, generated JSON, and
official-topology research scripts.
