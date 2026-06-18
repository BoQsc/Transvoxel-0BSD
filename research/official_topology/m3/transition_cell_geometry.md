# Transition-Cell Geometry

M3 uses the public topological transition cell:

- nine samples on the full-resolution face at `z = 0`;
- four samples on the half-resolution face at `z = 1`;
- half-resolution corner signs copied from full-resolution corners;
- four lateral faces joining corresponding perimeter edges.

The derivation permits intersection vertices on 16 public boundary edges:

- 12 horizontal or vertical edges in the full-resolution 3 by 3 grid;
- 4 perimeter edges of the half-resolution face.

M3 does not use the independent core's synthetic center sample. It also does not introduce vertices on full-face quadrant diagonals.

Candidate surfaces are built from the boundary loops:

- ordinary loops are triangulated as topological disks;
- nested coplanar loops are triangulated as annuli;
- every candidate is checked for nondegenerate triangles, exact boundary preservation, edge use greater than two, and detected nonadjacent triangle intersections.

This is sufficient to produce a valid candidate family. It is not sufficient to prove the official interior diagonal choices.
