# Clean-room rules

SPDX-License-Identifier: 0BSD

These rules apply to the public 0BSD core and its generators. The isolated
M23-M26 exact-compatibility work is a separate MIT-licensed research path
listed in `research/official_topology/MIT_ARTIFACTS.json`.

1. Do not open the official MIT `Transvoxel.cpp` table while editing public
   0BSD generator logic or generated output.
2. Do not paste official table values into issues, notes, comments, tests, or
   source files.
3. Public 0BSD tests must not require byte-for-byte equality with the MIT
   table. Isolated exact-compatibility tests may compare externally, but their
   committed 0BSD reports must remain aggregate-only.
4. Validate behavior with geometry tests and visual seam tests instead.
5. Keep the generator and generated output together.
6. If a human edits generated output by hand, delete it and regenerate.
7. If a better algorithm replaces the tetrahedral fan generator, document the
   new construction in `PROVENANCE.md`.
8. Exact oracle-calibrated selection data must carry an explicit MIT license
   and must never be copied into `include/`, `src/`, `generated/`,
   `core/independent/`, or the 0BSD distribution file list.
