# Implementation Survey

This document records what was checked outside this repository before treating the 0BSD core as a serious Transvoxel-style implementation candidate.

## Primary references

### Official Transvoxel overview

Source: https://transvoxel.org/

Important points used as requirements:

- The algorithm exists to stitch neighboring triangle meshes generated from voxel data at different resolutions.
- It inserts transition cells along boundaries where one side is sampled at one resolution and the other side is sampled at exactly half that resolution.
- It reduces the transition face state to nine high-resolution samples, giving 512 transition cases.
- The official table set groups those 512 cases into 73 equivalence classes.
- The intended result is to fill seams, cracks, and holes between different-resolution meshes.
- The page states the algorithm is free of patent claims.

### Dissertation

Source: https://transvoxel.org/Lengyel-VoxelTerrain.pdf

Important points used as requirements:

- Transition cells are local boundary cells inserted between regular cells of different resolutions.
- Regular cells are triangulated separately from transition cells.
- Transition cells use a fixed sample configuration and must connect full-resolution and half-resolution faces.
- The official presentation uses equivalence classes, geometric transformations, inversion handling, and winding reversal.

### Journal paper

Source: https://www.tandfonline.com/doi/abs/10.1080/2151237X.2011.563682

Important points used as requirements:

- The paper target is fast seamless stitching of triangle meshes generated from multiresolution voxel data.
- Transition cells are inserted between volumes of differing voxel resolutions.
- The method is marching-cubes-like but operates on voxel data at two different resolutions.

## Implementation examples checked

### Eric Lengyel Transvoxel repository

Source: https://github.com/EricLengyel/Transvoxel

The repository is the official data-table repository. It is MIT licensed and describes itself as containing data tables used in the Transvoxel Algorithm.

This 0BSD project intentionally does not copy, transform, translate, or byte-match that table file. It uses a clean generator and separate proof tools.

### Table-shape examples based on the official file

Example source: https://github.com/DXGatech/Smooth-Infinite-Voxel-Terrain/blob/master/transvoxel.cpp

This kind of implementation uses familiar Transvoxel table pieces such as:

- `regularCellClass[256]`
- `transitionCellClass[512]`
- `RegularCellData`
- `TransitionCellData`
- packed geometry counts and triangle indices
- inversion/winding flags

This 0BSD project currently exports a simpler table ABI:

- regular cases: 256
- transition cases: 512
- one direct class per case
- vertex references and triangle lists

That means the project is practical-drop-in as a small C core, but not byte/table-drop-in for consumers that expect Eric's exact table layout.

### Rust `transvoxel` crate

Source: https://docs.rs/transvoxel

Important points used as requirements:

- Users provide a density field and an isolevel.
- Adjacent rendered blocks should either have the same resolution or a 2:1 resolution relationship.
- When one block is lower resolution next to a higher-resolution block, the low-resolution side needs a transition face in that direction.
- Mesh extraction can be done per block, but the caller must manage LOD constraints.

This matches the direction for this project: a small engine-independent core plus external terrain/chunk policy.

### Godot Voxel Tools documentation

Source: https://voxel-tools.readthedocs.io/en/latest/smooth_terrain/

Important points used as requirements:

- Smooth voxel terrain is commonly represented by signed distance fields.
- The surface is the isolevel, usually zero.
- Transvoxel-style meshing is used for smooth terrain LOD in real Godot ecosystem practice.

This is why the validation suite uses several scalar/SDF-like fields and why Godot is used only as a validator/sandbox, not as the core product.

## What the survey proves

The external references agree on the important outcome:

- Transition cells must seal boundaries between 2:1 LOD meshes.
- The key external contract is absence of cracks/holes on the LOD seam.
- The method should be local enough for dynamic terrain edits.
- A practical implementation can expose a density/isolevel API and leave chunk LOD policy to the caller.

## What the survey does not prove

The survey does not prove this 0BSD project is identical to Eric Lengyel's implementation.

Known differences remain:

- It is not byte-for-byte compatible with the official MIT `Transvoxel.cpp`.
- It does not currently use the official 73 transition equivalence class compression.
- Its regular-cell generator is now a clean-room preferred-polarity modified-Marching-Cubes derivation proven behaviorally by M20; exact official class numbering, reuse codes, and table bytes are not claimed.
- It proves seam correctness and implementation usability, not identical triangulation topology or final visual art quality.
