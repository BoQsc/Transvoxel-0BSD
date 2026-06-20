# Transvoxel 0BSD

[![core-proof](https://github.com/BoQsc/Transvoxel-0BSD/actions/workflows/core.yml/badge.svg)](https://github.com/BoQsc/Transvoxel-0BSD/actions/workflows/core.yml)

Engine-independent, dependency-free C core for an independently generated **Transvoxel-style voxel LOD transition system** under 0BSD.

## Production recommendation

**Start with the official upstream MIT
[`Transvoxel.cpp`](https://github.com/EricLengyel/Transvoxel) as the initial
production backend.** Put it behind a stable project-owned adapter, then
establish long-term terrain, rendering, collision, editing, LOD, streaming,
and performance baselines.

Keep this 0BSD implementation as an optional comparison backend. Consider
switching only after it passes the same real-world acceptance tests against
that battle-tested baseline. The generated MIT exact artifacts in this
repository are proof and integration outputs; they are not preferred over
starting from the actual upstream implementation.

License boundary: the public core, generator/validation code, and aggregate
reports are 0BSD. The isolated exact oracle-calibrated artifacts in M24-M26
are explicitly MIT under [`LICENSES/MIT.txt`](LICENSES/MIT.txt) and are never
included in the 0BSD core package. See [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md).

## Why this is the default

The official upstream MIT implementation has the original topology and the
longest production history. Its license already permits commercial,
closed-source, and modified use when its copyright and permission notice are
preserved.

The 0BSD path is strongly tested and usable, but 170/256 regular cases and
373/512 transition cases use different valid interior connectivity. Use it
first only when independent 0BSD provenance is a hard requirement and the
integration can absorb the additional qualification. See
[`docs/CHOOSING_0BSD_OR_MIT.md`](docs/CHOOSING_0BSD_OR_MIT.md).

After choosing the 0BSD path, start with the small release asset rather than
the full proof repository:

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
Exact compatibility claim boundary: LOCKED by M22
Official oracle baseline: M23 compares all 256 regular and 512 transition cases
Exact oriented topology identity: PROVEN by M24 for all 256 + 512 cases
M24-M26 exact candidate data license: MIT / ISOLATED_FROM_0BSD_CORE
Compatible original Transvoxel.cpp data ABI: PROVEN by M25
Pinned Godot Voxel table-source integration: PROVEN by M26 with 781/781 records
Full Godot Voxel Windows GDExtension build with Zig: PASS by M26
Exact semantic drop-in integration: READY
Exact semantic drop-in 0BSD release: NOT_ACHIEVED by terminal M27 provenance decision
Roadmap: TERMINAL at M27; no automatic M28
Official numeric class IDs / byte table identity: NOT_PROVEN
```

The public core is **not** Eric Lengyel's MIT `Transvoxel.cpp` relicensed. It
is an independent 0BSD implementation. The full proof repository also contains
a clearly enumerated MIT exact-compatibility research track; those files are
not 0BSD and are not part of the public core.

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
RUN_M26.cmd         pinned Godot Voxel exact integration and full Zig build
RUN_M27.cmd         terminal exact-0BSD topology/provenance decision
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

The independent core is a usable product candidate, not a claim of equal
production history or equal per-case topology. M18 proves the published
transition reference convention and M19 proves published transition topology
behavior. M20 replaces the default regular table, and M21 selects the default
clean-room M4 transition table and proves public C/C++ functional consumer
compatibility. Exact table compatibility remains separate and currently
`NOT_PROVEN`.

The intended finish line was an exact 0BSD drop-in replacement for the official
table behavior and consumer surface without depending on the MIT data. M27 now
closes that goal as not achieved under this repository's clean-room provenance
standard. This is a terminal result, not an unbounded next milestone.

M24 proves exact edge-labeled oriented topology for every regular and
transition case in an isolated MIT candidate. The public default remains the
independently derived M21 0BSD functional table.

M25 adds an MIT-licensed exact `Transvoxel.cpp` data surface with the original
struct/symbol names and 16/56 class-array capacities. Its independent internal
class IDs, exact M24 topology, and formula-derived packed reuse codes pass an
unchanged-style C++ consumer. The public 0BSD default remains unchanged.

M26 replaces the table translation unit behind the actual pinned Godot Voxel
table API in a temporary build tree and compiles the same Godot-style consumer
against both implementations with Zig C++. All 256 regular cases, 512
transition cases, and 13 transition-corner records match. This proves the
exact semantic drop-in integration boundary. M26 also compiles and links the
complete pinned Godot Voxel Windows GDExtension with Zig, producing an
8,256,512-byte DLL in a temporary build. The generated exact candidate is MIT
because M24's triangulation selection indexes were calibrated by the MIT
oracle.

M27 reruns the independent 768-case comparison and audits the dissertation's
published rules. The deterministic independent topology matches exact oriented
topology in 86/256 regular and 139/512 transition cases. The publication fixes
robust boundary connectivity but permits multiple legal interior
triangulations; the exact M24-M26 candidate closes the remaining gaps with
MIT-oracle-calibrated choices. Those exact files are now explicitly MIT and
can be used under that license, but cannot be released as 0BSD. The functional
non-exact core remains exclusively 0BSD. There is no M28.

## What this proves

The current proof stack checks generator determinism, table validity, C compilation, release package contents, Godot seam metrics, and scripted automated terrain edits when run locally with Godot.

The proof does **not** claim:

```text
byte/table identity with Eric Lengyel's MIT Transvoxel.cpp
official 73-equivalence-class mapping
0BSD provenance clearance for the M24-M26 exact candidate; M27 records this as terminally not achieved
runtime Godot editor loading and visual terrain comparison for the exact candidate
finished game terrain visual quality
collision, streaming, materials, gameplay, or performance certification
```

A passing proof establishes the documented functional and boundary contract.
It does not make the 0BSD path the lower-risk default for existing production
consumers. See `docs/CHOOSING_0BSD_OR_MIT.md` for the operational choice.

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
docs/CHOOSING_0BSD_OR_MIT.md
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
