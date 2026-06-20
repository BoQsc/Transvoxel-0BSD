# GitHub Release Page Text

## Summary

This release packages an engine-independent, dependency-free C core for an independently generated **Transvoxel-style voxel LOD transition system** under 0BSD.

Use this release asset for embedding:

```text
transvoxel_0bsd_core.zip
```

The full repository includes generators, validators, Godot proof stages, scripted auto-interaction tests, and official-equivalence research reports.

For production, start with the official upstream MIT `Transvoxel.cpp` behind a
stable adapter. Keep this 0BSD core as an optional comparison backend and
switch only after equivalent long-term terrain, collision, editing, LOD,
streaming, and performance qualification. See
`docs/CHOOSING_0BSD_OR_MIT.md`.

## What is included in the core zip

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
include/transvoxel_m4_candidate.h
include/transvoxel_m4_backend.h
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
generated/official_topology_candidate_tables.h
examples/c_minimal/
examples/c_terrain_export/
examples/c_m4_backend_switch/
examples/c_m21_consumer_contract/
examples/cpp_consumer/
docs/API.md
docs/DROP_IN.md
docs/CHOOSING_0BSD_OR_MIT.md
docs/WHAT_THIS_PROVES.md
docs/C_COMPILER.md
docs/CORE_PACKAGE_CONTENTS.md
docs/KNOWN_LIMITS.md
docs/TESTING_BY_USERS.md
docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md
LICENSE
LICENSE_SCOPE.md
PROVENANCE.md
SOURCES.md
README_CORE.txt
```

## Current proof status

Expected proof state for this release line:

```text
independent 0BSD core: PASS
C core compile/run proof: PASS when a C compiler or Zig cc is available
Godot seam proof: PASS when RUN_FULL.cmd is run locally with Godot
scripted auto-interaction proof: PASS when RUN_FULL.cmd is run locally with Godot
release-candidate package check: PASS
MIT exact semantic topology/integration path: PROVEN by M24-M26
exact semantic 0BSD release: NOT_ACHIEVED by M27
official numeric class IDs and byte identity: NOT_PROVEN
```

This is an independent 0BSD implementation path. It is **not** Eric Lengyel's MIT `Transvoxel.cpp` relicensed, and it does not claim byte/table identity with official Transvoxel tables.

## Quick compile

With Zig:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

With a normal C compiler:

```sh
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

## Known limits

- Official numeric class IDs and byte identity remain `NOT_PROVEN`.
- The isolated MIT path has exact oriented topology and semantic integration;
  the public 0BSD package does not contain that data.
- The 0BSD core uses different valid interior connectivity in 170/256 regular
  and 373/512 transition cases, while matching tested seam boundaries.
- The current core is a proven independent Transvoxel-style candidate, not a
  table-ABI or exact-output clone of the official implementation.
- Visual/gameplay terrain quality still depends on the user's terrain system, materials, LOD policy, collision, editing rules, and streaming.

## Recommended feedback

Please open an issue if you test the core in another engine, compiler, operating system, or voxel terrain pipeline. Correctness reports are especially useful when they include generated mesh data, exact scalar field setup, LOD layout, and the smallest reproducible case.
