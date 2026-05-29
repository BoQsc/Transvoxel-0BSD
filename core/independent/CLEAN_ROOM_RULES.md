# Clean-room rules

SPDX-License-Identifier: 0BSD

1. Do not open the official MIT `Transvoxel.cpp` table while editing generator
   logic or generated output.
2. Do not paste official table values into issues, notes, comments, tests, or
   source files.
3. Do not write tests that require byte-for-byte equality with the MIT table.
4. Validate behavior with geometry tests and visual seam tests instead.
5. Keep the generator and generated output together.
6. If a human edits generated output by hand, delete it and regenerate.
7. If a better algorithm replaces the tetrahedral fan generator, document the
   new construction in `PROVENANCE.md`.
