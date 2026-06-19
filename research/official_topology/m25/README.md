# M25 - Compatible Vertex Encoding and Table Layout

M25 generates a research-only `Transvoxel.cpp` data surface with:

```text
RegularCellData
TransitionCellData
regularCellClass[256]
regularCellData[16]
regularVertexData[256][12]
transitionCellClass[512]
transitionCellData[56]
transitionCornerData[13]
transitionVertexData[512][12]
```

It uses independent internal class IDs, exact M24 topology, and geometric
formulas for packed reuse codes.

The generated data remains research-only and is not yet cleared for an 0BSD
release.
