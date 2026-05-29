# GitHub Release Page Text

## Summary

This release packages an engine-independent, dependency-free C core for an independently generated **Transvoxel-style voxel LOD transition system** under 0BSD.

Use this release asset for embedding:

```text
transvoxel_0bsd_core.zip
```

The full repository includes generators, validators, Godot proof stages, scripted auto-interaction tests, and official-equivalence research reports.

## What is included in the core zip

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
examples/c_minimal/
examples/c_terrain_export/
docs/API.md
docs/DROP_IN.md
docs/WHAT_THIS_PROVES.md
docs/C_COMPILER.md
docs/CORE_PACKAGE_CONTENTS.md
docs/KNOWN_LIMITS.md
LICENSE
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
official Transvoxel.cpp / 73-class equivalence: NOT_PROVEN
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

- Official 73-equivalence-class mapping is still research-only and `NOT_PROVEN`.
- Exact sign/orientation equivalence to MIT `Transvoxel.cpp` tables is `NOT_PROVEN`.
- The current core is a proven independent Transvoxel-style candidate, not a byte-compatible clone of the official table file.
- Visual/gameplay terrain quality still depends on the user's terrain system, materials, LOD policy, collision, editing rules, and streaming.

## Recommended feedback

Please open an issue if you test the core in another engine, compiler, operating system, or voxel terrain pipeline. Correctness reports are especially useful when they include generated mesh data, exact scalar field setup, LOD layout, and the smallest reproducible case.
