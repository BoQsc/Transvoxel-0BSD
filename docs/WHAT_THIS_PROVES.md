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

## Godot's role

Godot is used as a validator and interactive sandbox, not as the main product. The main product is the engine-independent C core.

## Not proven / not claimed

This project does not claim:

```text
byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp
field-for-field drop-in compatibility with every existing Transvoxel.cpp consumer
official 73-class transition compression
official topology equivalence for the optional M4 candidate backend
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

v25 adds a strict audit matrix. It checks internal duplicate/degenerate/winding/self-intersection conditions, but it still marks official 73-class/reference equivalence as `NOT_PROVEN`.

See `docs/PROOF_MATRIX.md` and `validation/strict_correctness_audit.json`.

## v26 audit timing note

`RUN_FULL.cmd` reruns the strict correctness audit after Godot seam metrics and auto-interaction are produced. This keeps the uploaded `SEND_TO_CHATGPT.zip` from carrying stale corner-junction status from the earlier Python-only proof phase.

## v29 official-equivalence research status

The proof gate now includes a separate official-equivalence research report. It confirms that the current project remains an independent 0BSD Transvoxel-style core, not a public-domain clone of the MIT table file. Naive 3x3 symmetry grouping does not reproduce the official 73 transition classes, so official equivalence remains a future topology-derivation problem.
