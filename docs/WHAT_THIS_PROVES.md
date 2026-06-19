# What this proves, and what it does not prove

## Proven by the package gates

The full proof package validates these things:

```text
regular and transition tables regenerate deterministically
exported transvoxel_tables ABI round-trips to canonical JSON
all 512 transition cases expose expected boundary contours
neighboring transition-cell side faces have matching fingerprints
sampled chunk strips have matching shared side-face fingerprints
Godot runtime and mesh API dumps can be produced
Godot seam metrics report seam_open_edges = 0
scripted auto-interaction edits keep the seam checks green
C core compiles and runs when a C compiler is available
M4 callback-adapter package example compiles and runs when a C compiler is available
default M4 terrain export and M4 callback-adapter terrain export compile and match when a C compiler is available
optional M4 candidate table is synced into the Godot data path and passes Godot-style metrics without executing Godot
optional M4 candidate table can feed a real Godot ArrayMesh/MeshDataTool viewer/export path when RUN_M11 is executed with Godot
default and optional M4 Godot transition-strip mesh paths can be compared side by side when RUN_M12 is executed with Godot
default and optional M4 Godot transition-strip mesh paths can be compared after scripted edits when RUN_M13 is executed with Godot
optional M4 candidate geometry, winding, ArrayMesh output, and side seams pass in all six explicit transition-face frames when RUN_M15 is executed
mapped M4 transition cells close shared lateral faces at three-face corners in all eight signed octants when RUN_M16 is executed
the M4-selected combined production gate passes when RUN_M17 is executed
the published M4 transition reference convention passes exhaustive Python and Zig C proof when RUN_M18 is executed
published M4 transition topology behavior passes all 512 cases when RUN_M19 is executed
the default clean-room regular-cell table passes preferred-polarity, neighbor-seam, M4-boundary, Zig C, and Godot proof when RUN_M20 is executed
the default clean-room M4 transition table and C/C++ consumer contract pass when RUN_M21 is executed
the exact compatibility claim boundary passes when RUN_M22 is executed
M4 replacement readiness is split into explicit machine-readable candidate/default/full/exact compatibility decisions
small dist/transvoxel_0bsd_core.zip can be built
```

The proof gate requires:

```text
seam_open_edges = 0
invalid_triangles = 0
degenerate_triangles = 0
failed_checks = 0
```

## Proven for users

The small core package proves that a user can copy these files into a normal C/C++/D/Godot/custom-engine build system:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
```

and call a plain C API with no Godot dependency.

The package also proves the M4 callback adapter can be compiled from package
files and installed explicitly through `transvoxel_m4_backend.h`. Since M21,
that adapter uses the same clean-room M4 topology source as the default
transition backend.

The C terrain export proof also checks the same terrain/LOD OBJ export path in
default mode and adapter mode. It confirms regular-cell output and transition
strip triangle counts match through the callback adapter.

The M4 Godot data-path proof checks that Godot can receive the M4 candidate
table as staged generated data and that the table satisfies the same non-visual
metrics shape used by the new M4 Godot stage. `RUN_M10.cmd` executes that stage
too when a Godot executable is available.

The M4 Godot viewer/export proof checks that the synced M4 candidate table can
build real Godot `ArrayMesh` objects for a case gallery and deterministic
terrain-strip-style mesh, and that `MeshDataTool` can read them back. This is
`RUN_M11.cmd`; it still keeps M4 optional.

The M4 Godot backend comparison proof checks that the default independent
transition table and the optional M4 candidate table can be selected explicitly
inside Godot, built through the same deterministic mesh path, and compared in a
report. This is `RUN_M12.cmd`; it still keeps the default backend as the
default.

The M4 Godot scripted edit comparison proof runs deterministic dig/add edits
over multiple fields and origins, then compares default and M4 transition-strip
mesh outputs after every edit. This is `RUN_M13.cmd`; it still keeps M4
optional.

The M4 replacement-readiness gate evaluates all accumulated evidence and
separates optional-backend readiness from default-backend replacement,
functional full replacement, and exact table compatibility. This is
`RUN_M14.cmd`.

The M4 six-face orientation proof validates all 512 cases in right-handed
`+X/-X/+Y/-Y/+Z/-Z` frames in Zig-compiled C and actual Godot runtime
execution. It checks transformed winding, `ArrayMesh`/`MeshDataTool`, and
deterministic neighboring-cell side seams. This is `RUN_M15.cmd`. It removes
the six-face blocker but does not prove the official frame convention.

The M4 corner-junction proof uses mapped sample positions for non-box transition
cells, coherent outward table winding, and three perpendicular transition
faces. Zig C and Godot both validate coincident lateral samples and geometry,
opposite boundary-edge winding, and a common inner corner across all eight
signed octants. This is `RUN_M16.cmd`.

The M4-selected production proof combines normal C backend installation, all
512 normal-API transition cases, mapped corner geometry in the same process,
terrain export, current Godot scripted edits, six-face/corner reports, and the
base production gate. This is `RUN_M17.cmd`. It proves readiness to replace the
default transition backend, not a full official-behavior replacement.

The M18 reference-convention proof maps the M4 row-major runtime case index to
the published Figure 4.17 index for all 512 cases. It validates sample
coordinates, negative-inside polarity, complement and D4 transforms, outward
winding, same-topology inverse winding, and all six face frames. This proves
the published algorithmic convention, not official triangle topology or table
bytes.

The M19 topology proof validates every published full-, half-, and lateral-face
contour rule, the D4/conditional-inversion class construction, closed degree-2
boundaries, and minimal genus-zero surface fillings for all 512 cases. It
proves functional transition topology behavior, not identical official
interior diagonals or table encoding.

The M20 regular-cell proof replaces the fixed-diagonal tetrahedral regular
table with a preferred-polarity modified-Marching-Cubes derivation. It proves
256 cases, 18 behavior classes, 12/5 vertex/triangle maxima, 12,288
regular-neighbor comparisons, 40,960 regular/M4 boundary comparisons, the
public C runtime, and actual Godot loading.

The M21 default-transition/consumer proof exports the default transition table
from the clean-room M4 published-topology source, validates 512 default cases,
4096 vertex refs, 2640 triangles, 12/12 transition maxima, C callback behavior,
sample-13 ABI retention, C++ include/link smoke, and actual Godot runtime
loading of the default transvoxel export.

The M22 exact-compatibility claim-boundary proof validates that product docs and
machine-readable reports allow the functional public C/C++ replacement claim
while separating MIT exact semantic data from the 0BSD core and identity
claims.

The M23 official-oracle baseline reads a verified external checkout of Eric
Lengyel's MIT `Transvoxel.cpp`, compares all 256 regular and 512 transition
cases, and records only hashes, counts, and mismatch categories. It proves that
the exact gap is measured. It does not itself prove exact replacement.

The M24 topology convergence proof keeps the independently derived boundary
loops, enumerates valid triangulations, and uses compact oracle-calibrated
selection indexes. The resulting isolated candidate matches exact oriented
edge-labeled topology for all 256 regular and 512 transition cases and runs
through the public C builder. It does not yet prove packed vertex/reuse
encoding, official class/table layout, provenance for a final public default,
or unchanged-consumer integration.

M24's generator code and aggregate reports are 0BSD. Its oracle-calibrated
generated rule/table data is explicitly MIT.

The M25 compatibility proof independently compresses the M24 topology into the
original 16/56 class-array capacities, derives packed regular/transition reuse
codes from geometry, emits the original struct and symbol names, and compiles
an unchanged-style C++ consumer across every case. It proves a compatible data
ABI, not numeric class-ID or byte identity. The generated exact file is MIT.

The M26 integration proof compiles the actual pinned Godot Voxel table API
against both its original table translation unit and the M25-backed replacement
with Zig C++. All 256 regular records, 512 transition records, and 13
transition-corner records match. This proves the exact semantic drop-in
integration boundary. M26 additionally compiles and links the complete pinned
Godot Voxel Windows GDExtension with Zig. Runtime editor loading is separate,
and the generated candidate is MIT because M24's exact filling selections were
oracle-calibrated.

The M27 terminal audit reruns the independent regular/transition generation,
the exhaustive 768-case official-oracle comparison, the exact M24-M26
candidate, the pinned Godot Voxel API comparison, and the full Zig GDExtension
build. It audits the official dissertation's published rules and the official
implementation's MIT license. The independent deterministic rule matches exact
oriented topology in 86/256 regular and 139/512 transition cases. Because the
publication permits multiple legal interiors and the exact candidate closes
the gaps with MIT-oracle-calibrated choices, M27 records that the exact 0BSD
replacement goal is not achieved. This is terminal; no M28 is selected.

## Godot's role

Godot is used as a validator and interactive sandbox, not as the main product. The main product is the engine-independent C core.

## Not proven / not claimed

This project does not claim:

```text
byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp
field-for-field compatibility with every possible Transvoxel.cpp fork
official numeric 73-class IDs
0BSD provenance clearance for the M24-M26 exact candidate; M27 terminally records this as not achieved
finished Godot gameplay terrain/GDExtension integration
a complete game terrain engine
chunk streaming
physics/collision generation
materials/texturing
performance certification
```

## Correct public description

Use this wording:

```text
Independent 0BSD Transvoxel-style voxel LOD transition core with generated
clean-room regular and M4 transition tables, plain C API, C/C++ consumer proof,
reproducible proof tools, Godot validation, and scripted automated interaction
tests.
```

Avoid this wording:

```text
Eric Lengyel's Transvoxel.cpp under public domain.
```

## v25 strict audit addition

v25 added the strict audit matrix. M18 marks the published reference convention
as `PROVEN`, and M19 marks published transition topology behavior as `PROVEN`.
Official class numbering, exact interior triangulation identity, vertex
encoding, and bytes remain `NOT_PROVEN`.

See `docs/PROOF_MATRIX.md` and `validation/strict_correctness_audit.json`.

## v26 audit timing note

`RUN_FULL.cmd` reruns the strict correctness audit after Godot seam metrics and auto-interaction are produced. This keeps the uploaded `SEND_TO_CHATGPT.zip` from carrying stale corner-junction status from the earlier Python-only proof phase.

## v29 official-equivalence research status

The proof gate now includes a separate official-equivalence research report. It confirms that the current project remains an independent 0BSD Transvoxel-style core, not a public-domain clone of the MIT table file. Naive 3x3 symmetry grouping does not reproduce the official 73 transition classes, so official equivalence remains a future topology-derivation problem.
