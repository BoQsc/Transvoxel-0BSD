# Correctness Argument

The public 0BSD core should be judged by its documented functional and boundary
contract, not by byte identity with the official MIT table file. The separate
MIT exact path should be judged by the stronger semantic compatibility evidence
from M24-M26.

## Required outcome

A Transvoxel-style terrain LOD core must be able to generate transition geometry between neighboring voxel meshes with a 2:1 resolution difference so that the boundary has no cracks or holes.

The strongest machine-readable condition is:

```text
seam_open_edges = 0
invalid_triangles = 0
degenerate_triangles = 0
failed_checks = 0
```

## Why table identity is not the public 0BSD proof target

The official Transvoxel repository contains data tables. Those tables are useful, but copying them would carry their license and provenance. This project instead proves the same type of external seam behavior through independent generation and validation.

Therefore, this project does not need to reproduce the exact official table bytes, table names, class ids, or packed encodings to be useful. It needs to prove that the generated meshes satisfy the same seam contract.

Usefulness is not the same as equal production risk. The 0BSD core uses
different valid interior connectivity in 170/256 regular and 373/512
transition cases. This can alter local rendered or collision surfaces while
preserving tested boundaries. See `docs/CHOOSING_0BSD_OR_MIT.md`.

## Proof layers in this repository

### 1. Generator determinism

The regular and transition tables regenerate from source scripts. Generated file hashes are recorded in proof reports.

### 2. Case coverage

The generated export contains:

```text
regular cases: 256
transition cases: 512
```

This matches the expected marching-cubes regular case count and the Transvoxel transition case count.

### 3. Boundary fingerprint proof

Every transition case exposes normalized boundary-segment fingerprints. These fingerprints are compared against expected high-resolution, low-resolution, and side-face boundary contours.

This proves internal boundary consistency of the generated clean-room table.

### 4. Neighbor proof

Side-face fingerprints are checked so adjacent transition cells expose matching contours when they share boundary signs.

This catches side cracks between transition cells in a strip.

### 5. Chunk-strip proof

Multiple deterministic scalar fields are sampled across transition-cell strips. Shared side faces are checked over many cases, fields, and seeds.

### 6. Godot runtime proof

Godot is used as an independent runtime validator, not as the product. The validator dumps runtime information, mesh API behavior, seam metrics, and scripted interaction metrics.

### 7. Automated interaction proof

Scripted dig/add edits are applied. Each edit triggers a seam check. The release gate requires zero failed checks.

### 8. C core compile proof

The small engine-independent C core is compiled and run when a compiler is available. On Windows, Zig can be used through `zig.exe cc`.

## What is proven strongly

When `RUN_FULL.cmd` passes, this project has proven:

- tables regenerate;
- the C core builds and runs;
- all 512 transition cases pass boundary checks;
- side-neighbor checks pass;
- deterministic chunk-strip checks pass;
- Godot seam metrics pass;
- scripted auto-interaction edits pass;
- public core zip builds.

## What is not proven

The proof does not claim:

- official 73-class compression;
- official numeric class IDs or byte identity;
- an exact 0BSD release of the M24-M26 MIT compatibility data;
- equal production history or equal integration risk between the two paths;
- final game terrain art quality;
- production collision/contact behavior;
- production performance in a large streaming world.

M24-M26 do prove identical oriented case topology and exact semantic downstream
integration for the isolated MIT path. M27 records that the exact data cannot
be represented as an all-0BSD replacement under the current provenance policy.

## Current verdict

The current project is best described as:

```text
An independently generated 0BSD Transvoxel-style voxel LOD transition core
that proves the main seam/transition outcome through exhaustive table checks,
Godot runtime validation, scripted edit validation, and C core compile tests.
```

For conservative production compatibility, start with the official upstream
MIT `Transvoxel.cpp`. Keep 0BSD behind the same adapter and switch only after
it passes equivalent long-term target-engine qualification.
