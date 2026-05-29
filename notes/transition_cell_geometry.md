# Transition-cell geometry used by this generator

SPDX-License-Identifier: 0BSD

The generator uses the sample numbering from the dissertation for the
full-resolution face:

```text
6 -- 7 -- 8
|    |    |
3 -- 4 -- 5
|    |    |
0 -- 1 -- 2
```

The half-resolution face has four corners:

```text
B -- C
|    |
9 -- A
```

The corner sign mapping is:

```text
9 == 0
A == 2
B == 6
C == 8
```

The generator then adds one synthetic center sample:

```text
M == sign of sample 4
```

This synthetic sample is not claimed to be part of the official Transvoxel
table. It exists so this repository can generate a deterministic transition-cell
surface by marching tetrahedra over a tetrahedral fan.

Boundary triangle groups:

- 8 triangles on the full-resolution face.
- 2 triangles on the half-resolution face.
- 3 triangles on each of the 4 lateral faces.
- Total: 22 boundary triangles.
- Each boundary triangle is connected to M, making 22 tetrahedra.
