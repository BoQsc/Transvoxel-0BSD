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
