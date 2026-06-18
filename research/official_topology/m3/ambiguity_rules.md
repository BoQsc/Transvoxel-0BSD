# Ambiguity Rules

The clean-room class derivation starts from D4 acting on the 3 by 3 full-resolution sample grid.

There are 51 D4 orbits whose representatives have four or fewer inside samples.

For a representative with no ambiguous full-resolution quadrant and no ambiguous half-resolution face, inversion is included in the same research class.

For a representative with ambiguity, inversion is excluded:

```text
51 base D4 classes
+18 inverse classes split by full-resolution ambiguity
+ 4 inverse classes split by half-resolution-only ambiguity
=73 research classes
```

The resulting 73 classes cover all 512 cases exactly once.

Important limits:

- research class IDs are not official class IDs;
- a matching class count is not a matching triangulation proof;
- transformed winding and vertex encodings are not derived in M3;
- official table identity remains `NOT_PROVEN`.

Case 341 exposes why interior topology cannot be chosen by a naive "one disk per boundary loop" rule. Its nested contours bound an annulus.
