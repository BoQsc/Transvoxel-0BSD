# Reference Convention Study

M18 proves the M4 candidate's equivalence to the published algorithmic
transition-cell convention without reading official lookup-table arrays.

## Published convention

The dissertation provides enough public information to define the convention:

- Section 4.3 and Figure 4.8 define the full-resolution, half-resolution, and
  lateral faces.
- Figure 4.10 classifies solid samples as inside and shows outward normals.
- Section 4.5 and Figure 4.16 number the 3 by 3 full-face samples `0..8` and
  half-face corners `9, A, B, C`.
- Section 4.5 and Figure 4.17 assign case-index weights to negative samples.
- Section 4.5 requires reversed triangle winding for inverted cases.

The M4 sample coordinates match Figure 4.16 directly. Its stable clean-room
runtime table uses row-major bits, so numeric case indexes are related by this
explicit permutation:

```text
sample:          0   1   2   3    4     5   6    7    8
local bit:      01  02  04  08   10    20  40   80  100
published bit:  01  02  04  80  100    08  40   20   10
```

The conversion is a bijection over all 512 cases. Numeric identity is not
claimed or required for behavioral convention equivalence.

## Proven by M18

- all 512 local-to-published and published-to-local mappings;
- complement mapping;
- Figure 4.17's 180-degree low-nibble/high-nibble transpose property;
- all 4096 D4 case-transform comparisons;
- full/half face and corner correspondence;
- negative values as inside/solid;
- coherent outward winding toward increasing scalar values;
- reversed winding for every complement pair sharing the same topology;
- orientation-preserving transforms through all six M4 face frames;
- the public C conversion helpers through Zig-compiled exhaustive execution.

## Still separate

M18 does not prove:

- official transition triangle topology for all 512 cases;
- official numeric 73-class IDs;
- official vertex/cache encoding;
- byte identity with `Transvoxel.cpp`.

Those remain separate gates because convention equivalence does not imply table
or triangulation identity.
