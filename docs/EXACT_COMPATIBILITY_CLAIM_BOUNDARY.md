# Exact Compatibility Claim Boundary

M22 locks the public claim boundary after M21.

Allowed public claim:

```text
Functional clean-room Transvoxel.cpp replacement through the public C/C++ API.
```

That means:

```text
default regular cells use the M20 clean-room preferred-polarity table
default transition cells use the M21 clean-room M4 published-topology table
C consumers can compile and run the public API
C++ consumers can include transvoxel.h and link against a C object
callback customization is retained
```

Not allowed without future exact evidence:

```text
Exact official Transvoxel.cpp table layout claim.
Official 73-class ID compatibility claim.
Official vertex/reuse encoding compatibility claim.
Exact official transition triangulation identity claim.
Exact official regular table identity claim.
Byte-for-byte Transvoxel.cpp table/file identity claim.
```

The M24 exact-topology result is allowed as a research claim, not as a released
0BSD product claim. M25 likewise allows a research claim of compatible original
data symbols, capacities, and reuse semantics. Release wording remains limited
until real integration and provenance gates pass.

Byte identity is not required for functional replacement. Byte identity is
required before claiming exact official table-file compatibility.

The boundary is machine-checked by:

```text
python tools/validate_exact_compatibility_claim_boundary.py
```

The expected report status is:

```text
PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY
```

Official arrays remain forbidden as generator inputs or copied data sources for
the shipped 0BSD product. The isolated M23 comparator may return aggregate
match/mismatch evidence but does not emit oracle table values.

## Active exact-replacement goal

The intended finish line is exact drop-in compatibility, not merely the
functional API claim. M23 therefore permits one isolated external-oracle
comparison process:

```text
read a verified external MIT Transvoxel.cpp checkout
compare all 256 regular and 512 transition cases
emit hashes, counts, and mismatch categories only
never copy or package oracle arrays in the 0BSD repository
```

Exact replacement means compatible topology, table fields/encodings, exported
symbols, and unchanged-consumer integration. Byte-identical source text is not
required.

## M24 topology rule boundary

M24 is an isolated research candidate. It retains the independently derived
boundary loops and enumerates valid triangulations without oracle data. The
verified oracle selects compact option indexes from that enumeration.

M24 proves:

```text
256/256 exact regular edge-labeled oriented topologies
512/512 exact transition edge-labeled oriented topologies
```

It does not yet authorize an exact replacement claim. The option-index
provenance must remain explicit, and official vertex ordering/reuse encoding,
class/table layout, and unchanged-consumer integration remain blocked.
The M24-generated rules and candidate tables are research-only and are not
marked as cleared 0BSD release data.

## M25 compatible data ABI boundary

M25 generates the original `Transvoxel.cpp` data structures, global symbol
names, and array capacities. It independently compresses M24 topology into 15
of 16 regular slots and 40 of 56 transition slots and derives packed reuse
codes from cell geometry.

M25 proves compatible symbol/layout/reuse semantics and unchanged-style C++
consumption. It does not claim Eric Lengyel's internal numeric class IDs or
table bytes. The generated data remains research-only under the unresolved
0BSD provenance gate.
