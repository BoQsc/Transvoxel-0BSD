# Public Release Candidate

This package has two audiences.

## Normal users

Choose the path before downloading. Use the MIT exact path for conservative
production compatibility, exact official topology, or existing table-layout
consumers. Use this 0BSD package when independent provenance is required and
the target terrain system can qualify the different interior connectivity.
See `docs/CHOOSING_0BSD_OR_MIT.md`.

For the 0BSD path, use:

```text
dist/transvoxel_0bsd_core.zip
```

That archive is the intended drop-in core package. It contains:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
include/transvoxel_m4_candidate.h
include/transvoxel_m4_backend.h
src/transvoxel_m4_candidate.c
src/transvoxel_m4_backend.c
generated/official_topology_candidate_tables.h
examples/c_minimal/
examples/c_terrain_export/
examples/c_m4_backend_switch/
examples/c_m21_consumer_contract/
examples/cpp_consumer/
docs/API.md
docs/DROP_IN.md
docs/CHOOSING_0BSD_OR_MIT.md
docs/WHAT_THIS_PROVES.md
docs/C_COMPILER.md
docs/CORE_PACKAGE_CONTENTS.md
docs/KNOWN_LIMITS.md
docs/TESTING_BY_USERS.md
docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md
LICENSE
LICENSE_SCOPE.md
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

This is an independent 0BSD Transvoxel-style transition core. It is not Eric Lengyel's MIT `Transvoxel.cpp` relicensed and does not claim byte-for-byte or field-for-field equivalence to the official data tables. It is usable, but it does not have identical interiors in every case or the same production history as the MIT exact path.
