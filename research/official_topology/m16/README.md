# M16: M4 deformed corner junctions

M16 implements and validates non-box transition-cell geometry for block edges
and corners.

The public transition-cell description requires adjacent transition cells to
share coincident lateral faces. At a corner, the full-resolution face remains
fixed while half-resolution corners are inset to make room for transition cells
on the other active faces.

M16 adds:

- coherent outward M4 triangle winding derived from the clean-room piecewise
  transition scalar interpolant;
- a mapped-position C builder for non-box transition cells;
- three-face junction tests for all eight signed corner octants;
- matching Zig C and actual Godot runtime evidence.

Run:

```text
RUN_M16.cmd
```

Public algorithmic source:

```text
Eric Lengyel, Voxel-Based Terrain for Real-Time Virtual Simulations,
Sections 4.3-4.4 and Figure 4.9.
https://transvoxel.org/Lengyel-VoxelTerrain.pdf
```

No official lookup-table arrays or values are used. Official table, class,
reference-convention, and topology equivalence remain unproven.
