# Public Release Candidate

This package has two audiences.

## Normal users

Use:

```text
dist/transvoxel_0bsd_core.zip
```

That archive is the intended drop-in core package. It contains:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
examples/c_minimal/
examples/c_terrain_export/
docs/API.md
docs/DROP_IN.md
docs/WHAT_THIS_PROVES.md
docs/C_COMPILER.md
LICENSE
PROVENANCE.md
SOURCES.md
README_CORE.txt
```

It does not require Godot. It does not include the large proof JSON files.

## Maintainers / auditors

Use the full repository package. It contains:

```text
tools/
generated/*.json
godot/stages/
validation/
research/official_topology/
RUN_FULL.cmd
RUN_FAST.cmd
RUN_CORE.cmd
RUN_AUTO.cmd
```

The full package exists so changes to the generator, tables, or core can be checked before release.

## Claim boundary

This is an independent 0BSD Transvoxel-style transition core. It is not Eric Lengyel's MIT `Transvoxel.cpp` relicensed and does not claim byte-for-byte or field-for-field equivalence to the official data tables.
