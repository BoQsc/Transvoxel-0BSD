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

The default regular and transition builders now use clean-room generated 0BSD tables. The M4 files are still included for explicit M4 direct/oriented/mapped APIs and for the callback-adapter smoke example, but the normal `tv_build_transition_cell()` default path is already the clean-room M4 published-topology table.

## Current status

```text
Independent 0BSD core: release-candidate track
Functional Transvoxel-style proof: PASS when the full proof gate passes
Default M4 transition backend: selected and validated by M21
M4 direct/adapter APIs: package-validated compatibility surfaces
M4 terrain export path: default and adapter modes validated through normal C API
Optional M4 Godot data path: metrics, backend/edit comparison, six-face orientation, and mapped corner junctions runtime-validated
Published transition reference convention: PROVEN by M18 through an explicit 512-case index bijection
Published transition topology behavior: PROVEN by M19 for all 512 cases
Clean-room regular-cell behavior: PROVEN and default regular table replaced by M20
Functional full replacement readiness: READY by M21 through public C/C++ API
Exact compatibility claim boundary: LOCKED by M22; exact official compatibility remains NOT_PROVEN
Official oracle baseline: M23 compares all 256 regular and 512 transition cases
Exact oriented topology identity: PROVEN by M24 for all 256 + 512 cases
M24 exact candidate release provenance: RESEARCH_ONLY / NOT_CLEARED_FOR_0BSD
Compatible original Transvoxel.cpp data ABI: PROVEN by M25
Exact replacement finish line: ACTIVE; next milestone is real engine integration/provenance
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
regular case=23 vertices=6 triangles=4
transition case=11 vertices=6 triangles=4
```

M4 callback-adapter package smoke:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c src/transvoxel_m4_candidate.c src/transvoxel_m4_backend.c examples/c_m4_backend_switch/main.c -o c_m4_backend_switch
./c_m4_backend_switch
```

M4 terrain export adapter smoke:

```sh
zig cc -std=c99 -Iinclude -Igenerated -DTV_EXAMPLE_USE_M4_BACKEND_CANDIDATE src/transvoxel.c src/transvoxel_m4_candidate.c src/transvoxel_m4_backend.c examples/c_terrain_export/main.c -o terrain_export_m4
./terrain_export_m4
```

## Small drop-in package contents

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
docs/WHAT_THIS_PROVES.md
docs/C_COMPILER.md
docs/CORE_PACKAGE_CONTENTS.md
docs/KNOWN_LIMITS.md
docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md
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
RUN_M8.cmd          M4 callback-adapter package proof
RUN_M9.cmd          M4 terrain export proof
RUN_M10.cmd         M4 Godot data-path metrics proof
RUN_M11.cmd         M4 Godot viewer/export mesh proof
RUN_M12.cmd         historical Godot default-vs-M4 comparison proof
RUN_M13.cmd         historical Godot default-vs-M4 scripted edit comparison proof
RUN_M14.cmd         M4 default/full replacement-readiness decision gate
RUN_M15.cmd         M4 all-six-face C/Godot orientation proof
RUN_M16.cmd         M4 mapped three-face corner-junction proof
RUN_M17.cmd         M4-selected combined production gate
RUN_M18.cmd         published reference-convention/index-mapping proof
RUN_M19.cmd         published transition-topology behavior proof
RUN_M20.cmd         clean-room regular-cell replacement/equivalence proof
RUN_M21.cmd         default M4 transition + C/C++ consumer compatibility proof
RUN_M22.cmd         exact compatibility claim-boundary proof
RUN_M23.cmd         exhaustive external official-oracle comparison
RUN_M24.cmd         exact regular/transition topology convergence
RUN_M25.cmd         compatible original data symbols/encoding/layout
```

After a local run, this file can be uploaded for debugging or confirmation:

```text
proof/SEND_TO_CHATGPT.zip
```

GitHub Actions run the generator/proof suite, default C smoke test, M4 callback-adapter package smoke test, M4 terrain export smoke test, dist build, release-candidate report, and GitHub-ready report. Godot runtime validation still needs a local machine with Godot installed.

## Project tracks

```text
core/independent/          proven practical 0BSD core candidate
research/official_topology/ no-copy research into official 73-class/topology equivalence
```

The independent core is the usable product candidate. M18 proves the published
transition reference convention and M19 proves published transition topology
behavior. M20 replaces the default regular table, and M21 selects the default
clean-room M4 transition table and proves public C/C++ functional consumer
compatibility. Exact table compatibility remains separate and currently
`NOT_PROVEN`.

The intended project finish line is now explicit: an exact drop-in replacement
for the official table behavior and consumer surface, without depending on the
MIT file at runtime. M23 establishes the isolated external-oracle baseline.
This does not mean copying or packaging the MIT arrays, and it does not require
byte-identical source text.

M24 now proves exact edge-labeled oriented topology for every regular and
transition case in an isolated research candidate. The public default remains
the M21 functional table until official-compatible vertex ordering/reuse
encoding, class/table layout, provenance, and unchanged-consumer integration
also pass.

M25 adds a research-only `Transvoxel.cpp` data surface with the original
struct/symbol names and 16/56 class-array capacities. Its independent internal
class IDs, exact M24 topology, and formula-derived packed reuse codes pass an
unchanged-style C++ consumer. The public 0BSD default remains unchanged while
real engine integration and provenance are unresolved.

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
docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md
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
