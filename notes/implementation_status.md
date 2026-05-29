# Implementation status

SPDX-License-Identifier: 0BSD

## v3 summary

The package now includes:

- canonical 256-case regular-cell table generation,
- canonical 512-case transition-cell table generation,
- topology and reproducibility validation,
- OBJ export for visual inspection,
- a Transvoxel table export layer,
- a validator proving that the Transvoxel table export round-trips back to canonical JSON,
- a minimal consumer demo.

## What v3 proves

v3 proves that this clean-room project can produce deterministic table data and
export it through a familiar table-driven lookup shape:

```text
case index -> class index -> class data -> vertex refs + triangles
```

This is useful groundwork for future drop-in compatibility.

## What v3 does not prove

v3 does not prove byte-for-byte identity with Eric Lengyel's MIT-licensed
`Transvoxel.cpp`, and it does not yet implement the official 73 transition
equivalence classes.

It also does not prove that the current experimental tetrahedral transition
triangulation is visually production-ready in a terrain engine.

## Next technical target

The next target should be engine-level seam validation:

1. build a small Godot/GDExtension or standalone C++ seam viewer,
2. feed it the Transvoxel header,
3. generate pairs of high/low LOD chunks around a shared boundary,
4. render stress cases,
5. record screenshots and failing case IDs.

Only after this should the table become a default implementation path.
