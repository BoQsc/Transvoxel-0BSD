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

  docs/CHOOSING_0BSD_OR_MIT.md
  docs/DROP_IN.md
  docs/API.md
  docs/WHAT_THIS_PROVES.md
  docs/C_COMPILER.md
  docs/EXACT_COMPATIBILITY_CLAIM_BOUNDARY.md

License: 0BSD.

This package contains no MIT exact-compatibility artifacts. See
LICENSE_SCOPE.md for the enforced boundary used by the full repository.

Important: this is an independent clean-room Transvoxel-style core. It is not a relicensed copy of Eric Lengyel's MIT Transvoxel.cpp and does not claim official 73-class table or byte identity.

Current public claim: functional Transvoxel.cpp replacement through public C/C++ API.

Production choice: use the MIT exact path when exact official topology,
existing table-consumer compatibility, or established production behavior is
the priority. Use this 0BSD core when independent provenance is required and
the target terrain system can qualify visual, collision, LOD, editing, and
performance behavior. The 0BSD path has different valid interior connectivity
in 170/256 regular and 373/512 transition cases. See
docs/CHOOSING_0BSD_OR_MIT.md.

M22 locks the exact compatibility claim boundary: exact official table layout,
73-class IDs, vertex/reuse encoding, triangulation identity, and byte identity
remain unclaimed.

The default regular-cell table is a clean-room preferred-polarity modified-Marching-Cubes derivation proven by M20. It uses 256 cases, 18 behavior classes, at most 12 vertices and 5 triangles.

The default transition-cell table is the clean-room M4 published-topology derivation selected and proven for the public API by M21. It uses 512 cases, at most 12 vertices and 12 triangles, and keeps the 14-sample public ABI while ignoring sample 13 in the default M4 path.

The package still includes explicit M4 direct/oriented/mapped APIs and the transvoxel_m4_backend.h callback adapter. Those files are compatibility and advanced-use surfaces, not a different default topology.
