# Transvoxel 0BSD

Engine-independent, dependency-free C core for an independently generated **Transvoxel-style voxel LOD transition system**.

The main public artifact is:

```text
dist/transvoxel_0bsd_core.zip
```

Copy the core into your project, feed scalar-field samples, and emit regular/transition triangles. Godot is included only as a validator and sandbox in the full package; it is not required by the C core.

## Status

```text
Independent 0BSD core: release-candidate track
Functional Transvoxel-style proof: PASS when RUN_FULL passes
Official Transvoxel.cpp / 73-class table equivalence: NOT_PROVEN
```

This is **not** Eric Lengyel's MIT `Transvoxel.cpp` relicensed. It is a clean-room 0BSD implementation path with generated tables, a plain C API, proof tools, Godot validation, and scripted auto-interaction tests.

## Small drop-in package

Use this for embedding:

```text
dist/transvoxel_0bsd_core.zip
```

Contents:

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
LICENSE
PROVENANCE.md
SOURCES.md
README_CORE.txt
```

## Quick compile

With Zig:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

With a normal C compiler:

```sh
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

## Full proof package

The full zip contains generators, validators, Godot stages, reports, and official-equivalence research.

Windows run modes:

```text
RUN_FAST.cmd        quick proof, no production claim
RUN_CORE.cmd        C core compile + dist package
RUN_GODOT.cmd       Godot validator + production gate
RUN_AUTO.cmd        headless scripted auto-interaction
RUN_FULL.cmd        full release proof
RUN.cmd             same as RUN_FULL.cmd
RUN_INTERACTIVE.cmd human sandbox evaluation
```

After a run, upload this file for debugging or confirmation:

```text
proof/SEND_TO_CHATGPT.zip
```

## Project tracks

```text
core/independent/          proven practical 0BSD core candidate
research/official_topology/ no-copy research into official 73-class/topology equivalence
```

The independent core is the usable product candidate. Official-equivalence research remains separate and currently `NOT_PROVEN`.

## Start here

```text
docs/DROP_IN.md
docs/API.md
docs/CORE_PACKAGE_CONTENTS.md
docs/WHAT_THIS_PROVES.md
docs/KNOWN_LIMITS.md
docs/PROJECT_TRACKS.md
```

## GitHub release helpers

For publishing, see:

```text
docs/GITHUB_RELEASE_PAGE.md
docs/GITHUB_PUBLISHING.md
docs/REPOSITORY_LAYOUT.md
CHANGELOG.md
```

The GitHub Actions workflow runs the generator/proof suite, C smoke test, dist build, release-candidate report, and GitHub-ready report. Godot runtime validation still needs a local machine with Godot installed.

