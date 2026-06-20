# Provenance

SPDX-License-Identifier: 0BSD

## Clean-room rule

The public files in `generated/` must be created by scripts in `tools/` from
this repository's canonical independent table generation process.

No values from Eric Lengyel's MIT-licensed `Transvoxel.cpp` lookup tables may be
copied, translated, reformatted, pasted, or manually transcribed into the
public 0BSD paths.

The isolated exact-compatibility artifacts listed in
`research/official_topology/MIT_ARTIFACTS.json` are the explicit exception:
they are MIT, not 0BSD. Aggregate M23-M27 reports remain 0BSD and contain no
exact arrays or oracle-selected indexes. See `LICENSE_SCOPE.md`.

## What the legacy independent transition generator does

`tools/generate_transition.py` still constructs a historical independent
transition-cell table as follows:

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

That legacy table remains available for historical comparison and validation,
but it is no longer the public default transition table.

## What the current default transition export does

M21 selects the clean-room M4 published-topology table as the public default
transition source:

```text
generated/official_topology_candidate_tables.json
```

`tools/export_transvoxel.py` exports that table into:

```text
generated/transvoxel_tables.json
generated/transvoxel_tables.h
generated/transvoxel_tables.d
```

The public transition ABI keeps 14 samples for compatibility, but the default
M4 table references samples 0 through 12 only. Sample 13 is ignored by the
default path.

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
- default transition source is the clean-room M4 published-topology table,
- no official 73-class packed layout,
- no copied packed encodings,
- no manually edited table values,
- generated output must round-trip back to the canonical JSON.

## Important limitation

The old independent transition table remains available as a historical artifact.
The default regular table no longer uses marching tetrahedra; M20 replaced it
with the clean-room preferred-polarity derivation. The default transition table
is the M21 clean-room M4 export. Exact official class numbering, reuse encoding,
triangulation identity, and table bytes are not claimed.

The default transition table is the M21 clean-room M4 export.

Exact official class numbering, reuse encoding, triangulation identity, and table bytes are not claimed.

M24-M26 exact-candidate boundary:

- M24 independently derives boundary loops and enumerates valid fillings, but
  the committed exact filling selections were calibrated against the external
  MIT oracle.
- M25 derives compatible struct/symbol capacities and packed reuse fields.
- M26 proves that candidate through the pinned Godot Voxel table API with zero
  mismatches across all 781 records and compiles/links the full Windows
  GDExtension with Zig in temporary clones.
- M27 exhaustively tests the independent deterministic rule and audits the
  published derivation. It records that the publication permits multiple legal
  interiors and that the exact authored choices are not uniquely selected by a
  public deterministic rule.
- The exact generated candidate is explicitly MIT and must not be labeled or
  distributed as 0BSD. The MIT copyright and permission notice must accompany
  copies or substantial portions. An exact 0BSD version would require explicit
  permission/relicensing or a new independent derivation.

Numeric class-ID identity and byte identity are not required for the semantic
drop-in finish line.

M22 machine-checks this exact compatibility claim boundary in
`validation/exact_compatibility_claim_boundary_report.json`.

M27 machine-checks the terminal provenance decision in
`validation/m27_terminal_roadmap_report.json`. This is an engineering
provenance decision for this repository, not legal advice.

## Acceptance policy before production use

A table generated here should not become the default terrain path until it passes
engine-level tests:

- no cracks on LOD seams,
- stable triangle winding,
- stable normals,
- no severe skinny-triangle artifacts near common terrain features,
- deterministic rebuilds,
- no visual regression compared with the current MIT-table implementation.

For the independent 0BSD path, production qualification must also cover
collision/contact behavior, repeated edits, LOD switching, streaming
boundaries, representative world-scale performance, and supported compilers.
The 0BSD proof does not transfer the MIT path's production history. Different
valid interior connectivity in 170/256 regular and 373/512 transition cases
must be treated as an explicit integration decision. See
`docs/CHOOSING_0BSD_OR_MIT.md`.

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
