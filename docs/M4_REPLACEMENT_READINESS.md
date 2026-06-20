# M4 Replacement Readiness

The project has four different readiness questions. They must not be collapsed
into one claim.

## 1. Optional transition-backend candidate

This requires the M4 table/runtime, C API, package, terrain export, Godot mesh,
backend comparison, and scripted edit milestones to pass.

Current status: machine-checked by
`validation/m4_replacement_readiness_report.json`.

## 2. Default transition-backend replacement

In addition to the candidate milestones, this requires:

```text
M4 validation in all six transition-face orientations
M4-specific multi-face/corner junction validation
the full production gate with M4 installed through the normal backend API
```

The first item is proven by M15, the second by M16, and the production gate by
M17. The readiness report now permits replacing the default transition backend.

## 3. Functional full Transvoxel.cpp replacement

In addition to default-backend readiness, this requires:

```text
independently proven published transition topology behavior
independently proven published sign/orientation/reference convention
clean-room regular-cell equivalence
a documented and tested consumer compatibility contract
```

The reference-convention item is proven by M18, transition topology behavior is
proven by M19, regular-cell equivalence is proven by M20, and
consumer compatibility/default transition selection is proven by M21.

Current status: functional full replacement is ready through the public C/C++
API. The default transition builder uses the clean-room M4 published-topology
table, while exact table/encoding/byte compatibility remains separate.

Byte-for-byte identity is not required for functional replacement.

M22 documents and machine-checks this claim boundary. After M22, the allowed
claim is functional replacement through the public C/C++ API. Exact official
table layout, 73-class IDs, vertex/reuse encoding, triangulation identity, and
byte identity remain blocked claims.

## 4. Exact table/encoding compatibility

This additionally requires:

```text
official 73-class ID mapping
official vertex/reuse encoding equivalence
exact table identity if that exact claim is made
```

Official table arrays must never be used as generator inputs or tuning oracles.

Run:

```text
RUN_M14.cmd
RUN_M15.cmd
RUN_M16.cmd
RUN_M17.cmd
RUN_M18.cmd
RUN_M19.cmd
RUN_M20.cmd
RUN_M21.cmd
RUN_M22.cmd
RUN_M23.cmd
RUN_M24.cmd
RUN_M25.cmd
RUN_M26.cmd
RUN_M27.cmd
```

The current expected result is a passing readiness analysis with the
functional full replacement decision ready, exact table-compatible identity
blocked, the M22 claim boundary documented, the M23 exhaustive oracle baseline
complete, M24 exact topology convergence proven, M25 compatible vertex
encoding/table layout proven, and M26 exact downstream source-contract
integration proven. M27 records the terminal exact-0BSD provenance decision.

The exact-replacement finish line requires field/output/symbol compatibility
and unchanged-consumer integration. It does not require byte-identical source
text.

After M24 passes, exact regular and transition edge-labeled oriented topology
is proven. Readiness then selects M25 exact vertex encoding and table layout.
The exact replacement decision remains blocked until those encodings and an
unchanged-consumer integration surface pass.

After M25 passes, compatible original data symbols, array capacities, packed
reuse semantics, and an unchanged-style C++ consumer are proven. Readiness
then selects M26 real engine integration and provenance. Numeric class-ID and
byte identity remain separate identity-only claims.

After M26 passes, the exact candidate matches all 781 records through the
pinned Godot Voxel table API and the complete Windows GDExtension compiles and
links with Zig. Readiness separates:

```text
exact semantic drop-in integration: READY
exact semantic drop-in 0BSD release: BLOCKED on provenance
numeric class IDs and byte identity: identity-only, not finish-line blockers
```

After M27, readiness is terminal:

```text
technical exact semantic integration: PROVEN
exact 0BSD replacement goal: NOT_ACHIEVED
functional non-exact 0BSD replacement: READY
next milestone: NONE_TERMINAL
```

The publication constrains robust boundaries but permits multiple legal
interiors. The independent deterministic rule does not match every authored
official interior, and the exact candidate uses MIT-oracle-calibrated choices.
Further review requires explicit permission/relicensing or a changed project
requirement; another automatic milestone cannot resolve this provenance fact.

## Production selection

Terminal readiness does not mean the two paths have equal risk. Use the MIT
exact path when exact official per-case topology, original table-consumer
compatibility, or established production behavior matters. Use the 0BSD path
when independent provenance is required and the project can qualify its
different interiors across visual output, collision, editing, LOD switching,
streaming, and performance.

The 0BSD path matches exact oriented topology in 86/256 regular and 139/512
transition cases; the other 170 regular and 373 transition cases use different
valid interiors while preserving the tested boundary contract. See
`docs/CHOOSING_0BSD_OR_MIT.md`.
