# Provenance

SPDX-License-Identifier: 0BSD

## Clean-room rule

The files in `generated/` must be created by scripts in `tools/` from this
repository's canonical table generation process.

No values from Eric Lengyel's MIT-licensed `Transvoxel.cpp` lookup tables may be
copied, translated, reformatted, pasted, or manually transcribed into this
repository.

## What this generator currently does

The transition generator constructs an independent transition-cell table as follows:

1. Use the nine full-resolution face samples numbered 0 through 8.
2. Derive the four half-resolution face corner signs from the matching
   full-resolution corner samples:
   - 9 from 0
   - A / 10 from 2
   - B / 11 from 6
   - C / 12 from 8
3. Add a synthetic center sample whose sign is derived from sample 4.
4. Triangulate the transition cell boundary into boundary triangles.
5. Connect every boundary triangle to the synthetic center sample, creating a
   tetrahedral fan.
6. Run marching tetrahedra over that tetrahedralization for all 512 possible
   sign configurations.
7. Emit the resulting edge-intersection vertices and triangles as canonical JSON,
   C, and D.

The regular generator independently derives a 256-case modified-Marching-Cubes
table:

1. Use the Figure 3.8 corner numbering and Listing 3.1 case bits.
2. Derive every cube-face contour with the public preferred-polarity rule.
3. Trace the resulting closed boundary loops.
4. Fill each loop with a minimal nonintersecting triangle disk.
5. Orient every connected component toward increasing scalar values.
6. Validate all 256 cases, 18 rotation/inversion behavior classes, regular-cell
   neighbors, and regular/M4 transition boundaries.

## Compatibility exporter

`tools/export_transvoxel.py` reads the canonical JSON files and
emits a Transvoxel lookup ABI:

```text
case index -> class index -> class data -> vertex refs + triangles
```

Current table export policy:

- direct one-class-per-case mapping,
- no official 73-class compression yet,
- no copied packed encodings,
- no manually edited table values,
- generated output must round-trip back to the canonical JSON.

## Important limitation

The old independent transition table remains available until M4 becomes the
default transition path. The default regular table no longer uses marching
tetrahedra; M20 replaced it with the clean-room preferred-polarity derivation.
Exact official class numbering, reuse encoding, and table bytes are not claimed.

## Acceptance policy before production use

A table generated here should not become the default terrain path until it passes
engine-level tests:

- no cracks on LOD seams,
- stable triangle winding,
- stable normals,
- no severe skinny-triangle artifacts near common terrain features,
- deterministic rebuilds,
- no visual regression compared with the current MIT-table implementation.

## Audit commands

```sh
python tools/generate_regular.py --out generated
python tools/generate_transition.py --out generated
python tools/export_transvoxel.py --out generated
python tools/verify_generated_tables.py
python tools/validate_transition.py
python tools/validate_tables.py
python tools/validate_transvoxel.py
```
