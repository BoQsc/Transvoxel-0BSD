# Sources

SPDX-License-Identifier: 0BSD

These are sources for the algorithmic idea and licensing/provenance decisions.
They are not copied lookup-table data.

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

## License references

- SPDX 0BSD page.
  https://spdx.org/licenses/0BSD.html

- Open Source Initiative 0BSD page.
  https://opensource.org/license/0bsd

- Creative Commons public-domain tools page for CC0 context.
  https://creativecommons.org/public-domain/

## Local policy

This repository uses 0BSD for software. CC0 may still be fine for assets or for
projects that explicitly want CC0, but 0BSD is the cleaner software license for
this generated code/table package.

## External review sources added in v24

- Official Transvoxel overview: https://transvoxel.org/
- Eric Lengyel dissertation: https://transvoxel.org/Lengyel-VoxelTerrain.pdf
- Journal paper DOI page: https://www.tandfonline.com/doi/abs/10.1080/2151237X.2011.563682
- Official data-table repository: https://github.com/EricLengyel/Transvoxel
- Rust transvoxel crate docs: https://docs.rs/transvoxel
- Godot Voxel Tools smooth terrain docs: https://voxel-tools.readthedocs.io/en/latest/smooth_terrain/

These sources are used for behavioral requirements and terminology only. This repository still does not copy or transform the MIT-licensed official table data.
