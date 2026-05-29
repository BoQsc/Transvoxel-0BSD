# Transvoxel 0BSD

[![core-proof](https://github.com/BoQsc/Transvoxel-0BSD/actions/workflows/core.yml/badge.svg)](https://github.com/BoQsc/Transvoxel-0BSD/actions/workflows/core.yml)

Engine-independent, dependency-free C core for an independently generated **Transvoxel-style voxel LOD transition system** under 0BSD.

## Use this first

Most users should start with the small release asset, not the full proof repository:

```text
dist/transvoxel_0bsd_core.zip
```

Download it from the latest GitHub release:

```text
https://github.com/BoQsc/Transvoxel-0BSD/releases
```

The small core package contains the public C API, generated tables, examples, docs, license, provenance notes, and sources list. Godot is **not** required by the core. Godot exists in this repository only as one validation and sandbox environment.

## Current status

```text
Independent 0BSD core: release-candidate track
Functional Transvoxel-style proof: PASS when the full proof gate passes
Official Transvoxel.cpp / 73-class table equivalence: NOT_PROVEN
```

This project is **not** Eric Lengyel's MIT `Transvoxel.cpp` relicensed. It is an independent 0BSD implementation path with generated tables, a plain C API, proof tools, Godot validation, scripted auto-interaction tests, and a separate official-topology research track.

## Quick compile

With Zig:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

With a normal C compiler:

```sh
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
```

Run the example:

```sh
./c_minimal
```

Expected kind of output:

```text
regular case=23 vertices=13 triangles=12
transition case=11 vertices=16 triangles=18
```

## Small drop-in package contents

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

## Full proof repository

Clone the full repository if you want to audit, regenerate, validate, or research the implementation.

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

After a local run, this file can be uploaded for debugging or confirmation:

```text
proof/SEND_TO_CHATGPT.zip
```

GitHub Actions run the generator/proof suite, C smoke test, dist build, release-candidate report, and GitHub-ready report. Godot runtime validation still needs a local machine with Godot installed.

## Project tracks

```text
core/independent/          proven practical 0BSD core candidate
research/official_topology/ no-copy research into official 73-class/topology equivalence
```

The independent core is the usable product candidate. Official-equivalence research remains separate and currently `NOT_PROVEN`.

## What this proves

The current proof stack checks generator determinism, table validity, C compilation, release package contents, Godot seam metrics, and scripted automated terrain edits when run locally with Godot.

The proof does **not** claim:

```text
byte/table identity with Eric Lengyel's MIT Transvoxel.cpp
official 73-equivalence-class mapping
finished game terrain visual quality
collision, streaming, materials, gameplay, or performance certification
```

See:

```text
docs/WHAT_THIS_PROVES.md
docs/KNOWN_LIMITS.md
docs/PROJECT_TRACKS.md
```

## Start here

```text
docs/DROP_IN.md
docs/API.md
docs/CORE_PACKAGE_CONTENTS.md
docs/WHAT_THIS_PROVES.md
docs/KNOWN_LIMITS.md
docs/PROJECT_TRACKS.md
```

## Release and publishing docs

```text
docs/GITHUB_RELEASE_PAGE.md
docs/GITHUB_PUBLISHING.md
docs/REPOSITORY_LAYOUT.md
CHANGELOG.md
```
