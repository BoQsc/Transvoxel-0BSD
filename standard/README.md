# Transvoxel table layer

The Transvoxel table export is a proof-oriented export format.

It is meant to show that the clean-room generator can be consumed through a familiar Transvoxel lookup pattern:

```text
case index -> class index -> class data -> vertex refs + triangles
```

Generated files:

```text
generated/transvoxel_tables.json
generated/transvoxel_tables.h
generated/transvoxel_tables.d
```

Validation files:

```text
validation/transvoxel_report.json
validation/transvoxel_report.md
```

## Current status

This is a **proof table ABI**, not a byte-for-byte or field-for-field clone of Eric Lengyel's MIT-licensed `Transvoxel.cpp`.

Current differences from the official table file:

- direct one-class-per-case mapping instead of 73 transition equivalence classes,
- clean-room vertex-reference format instead of the official packed values,
- generated C/D names use the `tvc_` / `TVC` prefix,
- table data is generated from this repository's canonical JSON only.

## Why this exists

The main engine can use the clean canonical format, while future tests can target a more traditional class/data table access pattern. That gives a migration path toward stricter drop-in behavior without contaminating the generator with copied table values.
