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

Not allowed as an 0BSD release or identity claim:

```text
Exact official Transvoxel.cpp table layout claim.
Official 73-class ID compatibility claim.
Byte-for-byte Transvoxel.cpp table/file identity claim.
0BSD release claim for the M24-M26 exact candidate.
```

The M24 exact-topology result is allowed as a research claim, not as a released
0BSD product claim. M25 likewise allows a research claim of compatible original
data symbols, capacities, and reuse semantics. Release wording remains limited
because M27 terminally records that the exact-candidate provenance gate does
not pass under the current clean-room policy.

Byte identity is not required for functional replacement. Byte identity is
required before claiming exact official table-file compatibility.

Research-only exact topology, packed reuse semantics, and downstream
integration claims are permitted by M24-M26. They do not authorize an 0BSD
release of the generated exact candidate.

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

## Terminal exact-replacement outcome

The intended finish line was exact 0BSD drop-in compatibility, not merely the
functional API claim. M23 therefore permitted one isolated external-oracle
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

M27 closes the exact 0BSD finish line as not achieved. The independent
deterministic rule reaches 86/256 regular and 139/512 transition exact oriented
topology matches. The publication explicitly permits multiple legal interiors,
so its normative rules do not uniquely select all authored official choices.
M24 reaches exact topology only through MIT-oracle-calibrated option indexes.
There is no M28; a new review requires explicit permission/relicensing or a
changed project requirement.

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

## M26 downstream integration boundary

M26 generates a replacement for the table translation unit used by the pinned
Godot Voxel checkout. The same Zig-compiled Godot-style consumer is built
against the unmodified downstream table file and the M26 replacement.

M26 proves:

```text
256/256 regular output records match
512/512 transition output records match
13/13 transition corner reuse records match
packed reuse fields and oriented triangle output match
actual Godot Voxel table namespace/accessor contract compiles
full pinned Godot Voxel Windows GDExtension compiles and links with Zig
```

This establishes exact semantic drop-in integration. It is not a byte-identity
claim and does not require official numeric class IDs. Runtime editor loading
and visual terrain comparison remain separate from this compile/link proof.

The exact candidate remains research-only because M24's option indexes were
oracle-calibrated. M27 confirms that provenance is terminally uncleared under
the current policy. The functional clean-room Transvoxel.cpp replacement
through the public C/C++ API remains available under 0BSD.
