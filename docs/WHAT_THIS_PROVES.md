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
optional M4 candidate backend package example compiles and runs when a C compiler is available
optional M4 candidate backend terrain export compiles and runs when a C compiler is available
optional M4 candidate table is synced into the Godot data path and passes Godot-style metrics without executing Godot
optional M4 candidate table can feed a real Godot ArrayMesh/MeshDataTool viewer/export path when RUN_M11 is executed with Godot
default and optional M4 Godot transition-strip mesh paths can be compared side by side when RUN_M12 is executed with Godot
default and optional M4 Godot transition-strip mesh paths can be compared after scripted edits when RUN_M13 is executed with Godot
optional M4 candidate geometry, winding, ArrayMesh output, and side seams pass in all six explicit transition-face frames when RUN_M15 is executed
mapped M4 transition cells close shared lateral faces at three-face corners in all eight signed octants when RUN_M16 is executed
the M4-selected combined production gate passes when RUN_M17 is executed
the published M4 transition reference convention passes exhaustive Python and Zig C proof when RUN_M18 is executed
published M4 transition topology behavior passes all 512 cases when RUN_M19 is executed
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

The package also proves an optional M4 candidate backend can be compiled from
package files and installed explicitly through `transvoxel_m4_backend.h`.
That candidate path is still separate from the default backend.

The C terrain export proof also checks the same terrain/LOD OBJ export path with
M4 installed. It confirms regular-cell output is unchanged while the transition
strip uses the installed M4 backend.

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

## Godot's role

Godot is used as a validator and interactive sandbox, not as the main product. The main product is the engine-independent C core.

## Not proven / not claimed

This project does not claim:

```text
byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp
field-for-field drop-in compatibility with every existing Transvoxel.cpp consumer
official numeric 73-class IDs
exact official interior triangulation identity for the optional M4 candidate backend
finished Godot gameplay terrain/GDExtension integration through the optional M4 candidate backend
a complete game terrain engine
chunk streaming
physics/collision generation
materials/texturing
performance certification
```

## Correct public description

Use this wording:

```text
Independent 0BSD Transvoxel-style voxel LOD transition core with generated tables,
plain C API, reproducible proof tools, Godot validation, and scripted automated
interaction tests.
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
