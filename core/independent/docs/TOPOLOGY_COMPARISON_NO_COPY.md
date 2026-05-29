# Topology Comparison Without Copying Tables

This project can compare topology-level facts without using MIT table values.

## Safe comparison data

- counts: 256 regular cases, 512 transition cases, 73 official transition classes;
- constraints: 2:1 LOD boundary, transition face on low-resolution side;
- boundary fingerprints: high face, low face, and four side faces;
- triangle graph properties: degenerate triangles, duplicate triangles, non-manifold side seams, self-intersections;
- class orbit counts from independently defined transforms.

## Unsafe comparison data

- official table arrays;
- packed official vertex data;
- official class IDs;
- official triangle index sequences;
- exact official case-to-class mapping.

## v29 comparison result

The v29 research script computes naive bit-pattern symmetry orbit counts:

- C4 rotations only;
- C4 rotations plus complement;
- D4 rotations/reflections only;
- D4 rotations/reflections plus complement.

None of those equals 73. This is useful: it warns us that official 73-class equivalence cannot be reconstructed by a trivial 3x3-grid symmetry pass alone.

