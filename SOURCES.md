# Sources

SPDX-License-Identifier: 0BSD

These are sources for the algorithmic idea and licensing/provenance decisions.
The public 0BSD core contains no copied lookup-table data. Exact
oracle-calibrated artifacts are separately enumerated and MIT licensed.

## Transvoxel / transition-cell references

- Eric Lengyel, "Voxel-Based Terrain for Real-Time Virtual Simulations",
  PhD dissertation, University of California at Davis, 2010.
  https://transvoxel.org/Lengyel-VoxelTerrain.pdf

- Eric Lengyel, "Transition Cells for Dynamic Multiresolution Marching Cubes",
  Journal of Graphics, GPU, and Game Tools, Vol. 15, No. 2, 2010.
  DOI: 10.1080/2151237X.2011.563682

- Public Transvoxel overview page.
  https://transvoxel.org/

The public overview page states that the Transvoxel Algorithm is free of patent
claims. The dissertation describes the transition cell as having a
full-resolution face with nine samples, an opposite half-resolution face whose
corner values equal the matching full-resolution corners, and 512 possible
case-index configurations.

M18 uses the dissertation's public Section 4.3, Figures 4.8 and 4.10, and
Section 4.5, Figures 4.16 and 4.17, to derive sample coordinates, full/half face
semantics, negative-inside polarity, case-index bit weights, outward winding,
and inversion behavior. It does not use the official lookup-table arrays.

M20 uses dissertation Section 3.1.2 and Figure 3.5 for preferred-polarity face
contours, Figure 3.8 and Listing 3.1 for regular-corner numbering and case bits,
and Section 3.2 for the active-edge, 12-vertex, and 5-triangle limits. No
official regular lookup-table arrays are used.

M21 uses the clean-room M4 published-topology table proven by M18/M19 as the
default transition source and the clean-room regular table proven by M20 as the
default regular source. It proves the public C/C++ functional consumer contract.
No official transition or regular lookup-table arrays are used.

M22 uses the M21 evidence only to lock the public claim boundary. It does not
use official lookup-table arrays and does not create any new exact official
compatibility claim.

M23 uses a pinned external MIT checkout only as an isolated comparison oracle:

- origin: `https://github.com/EricLengyel/Transvoxel.git`
- commit: `51a494f03c5b024cd153b596bcc7152eb3cc93a6`
- `Transvoxel.cpp` SHA-256:
  `83a5511346b54c42e4e66dec916d3971c92f4fbda1c7878cbad5901a820dcab4`

M26 uses a pinned local Godot Voxel checkout as a downstream integration
consumer:

- origin: `https://github.com/Zylann/godot_voxel.git`
- commit: `d46c11c045493da31e2410f4a0eff429f9ff8f89`
- `meshers/transvoxel/transvoxel_tables.cpp` SHA-256:
  `836cde5412740d9acb39dcc409c696fa1dd61ffd4a23cafcacd091fb26e93fe2`

The downstream source is copied only into temporary test trees. It is not
packaged as 0BSD.

The M26 full build uses the local Godot 4.5 `godot-cpp` API/header package and
prebuilt Zig-compatible debug library. The recorded static-library SHA-256 is:

`1f892f805b88f855ad8e14f0e2be655af08ac7ae3cbf837a6ba0d846648ac9fb`

M27 audits the official dissertation downloaded from the URL above:

- file SHA-256:
  `c1c86dc1c441fa86dbe6b4b38a521ffb26a5eec3c4eede0f5782508a6ad41160`
- PDF pages 24-25: modified Marching Cubes allows any robust minimal cell
  triangulation and fixes preferred-polarity boundary connectivity;
- PDF pages 39-40: regular classes can have multiple legal interiors and the
  illustrated alternatives are chosen for curvature contrast;
- PDF pages 46 and 51-52: transition class IDs are somewhat arbitrary and
  boundary rules constrain the cell while exact interiors are illustrated.

These primary-source constraints do not uniquely select every official
interior diagonal. M27 combines that finding with the exhaustive oracle
comparison; it does not copy dissertation figures or official lookup arrays.

## License references

- SPDX 0BSD page.
  https://spdx.org/licenses/0BSD.html

- Open Source Initiative 0BSD page.
  https://opensource.org/license/0bsd

- Creative Commons public-domain tools page for CC0 context.
  https://creativecommons.org/public-domain/

## Local policy

The independent public core, generators, and aggregate reports use 0BSD. Exact
selection-bearing M24-M26 artifacts use MIT; see `LICENSE_SCOPE.md`.
This provenance split does not imply equal production behavior or risk. The
engineering selection guidance is in `docs/CHOOSING_0BSD_OR_MIT.md`.

## External review sources added in v24

- Official Transvoxel overview: https://transvoxel.org/
- Eric Lengyel dissertation: https://transvoxel.org/Lengyel-VoxelTerrain.pdf
- Journal paper DOI page: https://www.tandfonline.com/doi/abs/10.1080/2151237X.2011.563682
- Official data-table repository: https://github.com/EricLengyel/Transvoxel
- Rust transvoxel crate docs: https://docs.rs/transvoxel
- Godot Voxel Tools smooth terrain docs: https://voxel-tools.readthedocs.io/en/latest/smooth_terrain/

These sources are used for behavioral requirements and terminology in the
0BSD core. The separately listed exact-compatibility artifacts are explicitly
MIT and are excluded from the 0BSD package.
