# Official-Equivalence Research Track

This document defines the research track for proving whether this 0BSD project behaves like, or can be mapped to, the original Transvoxel table system without copying the MIT-licensed table data.

## Goal

The goal is not to relicense Eric Lengyel's `Transvoxel.cpp`. The goal is to independently prove, as far as possible, that this project satisfies the same public algorithmic contract:

- transition cells stitch LOD0 and LOD1 voxel meshes;
- adjacent blocks are equal resolution or 2:1 resolution;
- the low-resolution block owns a transition face toward the high-resolution block;
- the transition case index covers 512 possible sign cases;
- the original algorithm describes 73 transition equivalence classes;
- winding and sign convention are internally consistent and can be mapped to a documented convention.

## Safe research boundary

Allowed:

- Reading the dissertation/paper and public explanatory pages.
- Reading public documentation of implementations to understand API shape and expected outcomes.
- Recording structural facts such as `512 cases`, `73 classes`, `transition face`, `2:1 LOD`, and `low-to-high neighbor direction`.
- Writing independent validators and deriving our own class/grouping logic.
- Comparing our own generated outputs to our own independently derived signatures.

Not allowed in this project:

- Copying Eric Lengyel's MIT table values.
- Translating official table arrays to another language.
- Using official table data as golden output.
- Editing our tables until they match official numeric arrays.

## Current result

As of v29:

- Functional Transvoxel-style proof is strong and automated.
- Official equivalence is **not proven**.
- Naive bit-pattern symmetry groups do not reproduce the official 73 classes.
- This means the official 73-class mapping is not merely a trivial 3x3-grid D4/C4/complement grouping; it likely depends on transition-cell triangulation/topology details.

## Next actual research tasks

1. Derive an independent canonical transition-cell topology from the dissertation diagrams and text.
2. Define a reference sign convention in our own words.
3. Derive candidate equivalence classes from topology signatures, not copied table values.
4. Prove every 512 case maps through a documented transform to a candidate class.
5. Compare topology-level invariants, not MIT table bytes:
   - boundary contours,
   - triangle adjacency graphs,
   - winding parity,
   - vertex interpolation edge categories,
   - high/low/side-face fingerprints.
6. Only after the above should we consider a Transvoxel.cpp-style exporter.

## Claim wording

Safe claim:

> Independent 0BSD Transvoxel-style voxel LOD transition core with automated seam, edit, and core compile proof.

Unsafe claim:

> Public-domain clone of Eric Lengyel's Transvoxel.cpp.


## v30 topology-signature result

v30 derives topology signatures for all 512 generated transition cases without
copying or reading official MIT table values.

The generated topology signatures do not collapse to the public official target
of 73 classes. The closest tested count was 51 from raw D4+complement sign-bit
orbits, while the generated sample-edge topology signatures produced 201 classes
under D4 and complement canonicalization.

This is a useful negative result: the current generator remains a strongly tested
independent Transvoxel-style transition system, but official 73-class/topology
equivalence remains **NOT_PROVEN**.
