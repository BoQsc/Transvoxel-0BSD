# M25 - Compatible Vertex Encoding and Table Layout

M25 generates an MIT-licensed exact `Transvoxel.cpp` data surface with:

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

The generated exact data is MIT under `LICENSES/MIT.txt`. The generator and
aggregate validation report are 0BSD.
