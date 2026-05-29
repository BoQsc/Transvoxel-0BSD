# Godot validation handoff

SPDX-License-Identifier: 0BSD

Goal: test whether these 0BSD-generated tables are usable for your terrain project without claiming compatibility with the official MIT table.

Recommended integration path:

1. Add a feature flag, for example `USE_CLEANROOM_TET_LOD_TABLES`.
2. Keep the current terrain meshing path unchanged.
3. Add a separate debug mesher that reads the generated table arrays.
4. Test only a small flat world first.
5. Then test SDF spheres, diagonal planes, cave mouths, and edited seam chunks.
6. Render seam chunks with wireframe overlays.
7. Log cracks by comparing boundary vertex positions between regular and transition chunks.
8. Do not switch production terrain over until the debug branch proves no visible holes.

Recommended test shapes:

- horizontal plane,
- vertical plane crossing the LOD seam,
- diagonal plane crossing the LOD seam,
- sphere centered on the LOD seam,
- cave mouth tangent to the LOD seam,
- random smooth noise with fixed seed,
- destructive edits exactly on the seam.

Pass criteria:

- no sky cracks,
- no doubled faces at the seam,
- no inverted triangles visible in wireframe,
- stable output after repeated edits,
- deterministic rebuild from the same voxel samples.

Failure handling:

If cracks appear, keep the repository structure and provenance rules, but replace the generator algorithm. Do not patch generated values by hand.
