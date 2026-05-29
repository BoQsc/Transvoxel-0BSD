# Proof Method

This repository now separates proof into four levels.

## 1. Reproducibility

`tools/prove_tables.py` regenerates the tables and checks that the generated
outputs match the committed/generated JSON contract.

## 2. Table ABI proof

`tools/validate_transvoxel.py` checks that `generated/transvoxel_tables.*` is a
lossless export of the canonical JSON tables.

## 3. Boundary proof

`tools/validate_boundaries.py` checks all 512 transition cases. For each case it
extracts the actual open boundary edges of the generated triangle mesh and
compares them to the contour that should appear on the documented boundary
triangles of the transition cell.

Pass condition:

```text
actual boundary segments == expected boundary contour segments
```

This catches missing boundary segments, extra boundary segments, and cracked
cell borders.

## 4. Neighbor and chunk-strip proof

`tools/validate_neighbors.py` proves that side-face contours are a pure function
of the shared side-face signs.

`tools/validate_chunks.py` samples deterministic sign fields over many small
transition-cell strips and checks every shared side face between neighboring
transition cells.

This is still table-level proof. The next external proof is a Godot runtime
scene with real chunk meshes, wireframe rendering, and open-edge counting.

## What this does not prove

This package does not prove byte-for-byte identity with Eric Lengyel's
MIT-licensed `Transvoxel.cpp`. It also does not yet prove the official
73-equivalence-class compression.
