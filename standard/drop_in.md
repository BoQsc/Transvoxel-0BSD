# Drop-in roadmap

Goal: keep the 0BSD clean-room generator while allowing stricter table exports later.

## Level 0: Clean canonical tables

Already present. The generator produces deterministic regular and transition case tables.

## Level 1: Transvoxel access pattern

Added in v3. Export tables using:

```text
case index -> class index -> class data -> vertex refs + triangles
```

This proves the data can be consumed through a classic table-driven mesher shape.

## Level 2: Stable external ABI

Next target. Freeze the C/D struct names, constants, and index types so engine code can depend on them.

## Level 3: Standard Transvoxel semantics

Future target. Replace the experimental tetrahedral transition triangulation with a closer implementation of the transition-cell cases described in the dissertation and public Transvoxel materials.

## Level 4: 73-class compression

Future target. Implement clean-room symmetry generation and compression so the 512 transition cases map into 73 equivalence classes with inversion/winding handling.

## Level 5: stricter drop-in adapter

Future target. Generate a Transvoxel header/source shaped for existing Transvoxel meshers. This still must be generated from our own canonical data, not by copying or translating the MIT table file.
