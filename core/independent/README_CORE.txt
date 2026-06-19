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
  examples/c_m4_backend_switch/  M4 callback-adapter smoke
  examples/c_m21_consumer_contract/
  examples/cpp_consumer/

Read first:

  docs/DROP_IN.md
  docs/API.md
  docs/WHAT_THIS_PROVES.md
  docs/C_COMPILER.md

License: 0BSD.

Important: this is an independent clean-room Transvoxel-style core. It is not a relicensed copy of Eric Lengyel's MIT Transvoxel.cpp and does not claim official 73-class table or byte identity.

The default regular-cell table is a clean-room preferred-polarity modified-Marching-Cubes derivation proven by M20. It uses 256 cases, 18 behavior classes, at most 12 vertices and 5 triangles.

The default transition-cell table is the clean-room M4 published-topology derivation selected and proven for the public API by M21. It uses 512 cases, at most 12 vertices and 12 triangles, and keeps the 14-sample public ABI while ignoring sample 13 in the default M4 path.

The package still includes explicit M4 direct/oriented/mapped APIs and the transvoxel_m4_backend.h callback adapter. Those files are compatibility and advanced-use surfaces, not a different default topology.
