Transvoxel 0BSD Core
====================

This is the small engine-independent C package.

Use these files:

  include/transvoxel.h
  src/transvoxel.c
  generated/transvoxel_tables.h

Examples:

  examples/c_minimal/
  examples/c_terrain_export/
  examples/c_m4_backend_switch/  optional M4 candidate backend

Read first:

  docs/DROP_IN.md
  docs/API.md
  docs/WHAT_THIS_PROVES.md
  docs/C_COMPILER.md

License: 0BSD.

Important: this is an independent Transvoxel-style transition core. It is not a relicensed copy of Eric Lengyel's MIT Transvoxel.cpp and does not claim official 73-class table equivalence.

Optional: the package includes an M4 official-topology candidate backend. It must be compiled and installed explicitly with transvoxel_m4_backend.h. It is not the default backend and still does not prove official Transvoxel.cpp equivalence.

For terrain-style smoke testing, examples/c_terrain_export can be compiled with TV_EXAMPLE_USE_M4_BACKEND_CANDIDATE and the optional M4 source files.
