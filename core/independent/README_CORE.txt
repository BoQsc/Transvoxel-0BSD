Transvoxel 0BSD Core
====================

This is the small engine-independent package.

Copy these files into your project:

  include/transvoxel.h
  src/transvoxel.c
  generated/transvoxel_tables.h

Compile src/transvoxel.c together with your engine code and add these include paths:

  -Iinclude
  -Igenerated

There are no Godot dependencies and no third-party dependencies.

Minimal Zig build:

  zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal.exe

Minimal cc build:

  cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal

Examples:

  examples/c_minimal/main.c
    Builds one regular cell and one transition cell.

  examples/c_terrain_export/main.c
    Exports a tiny OBJ file from repeated core calls. It is deliberately simple
    and duplicates vertices so the example stays easy to read.

Docs:

  docs/DROP_IN.md
  docs/API.md
  docs/WHAT_THIS_PROVES.md

Honest status:

  This is an independent 0BSD Transvoxel-style core. It is not Eric Lengyel's
  MIT Transvoxel.cpp relicensed or copied. Use the full package for generators,
  provenance notes, and proof tools.

External review note:

The full package includes `docs/IMPLEMENTATION_SURVEY.md`, `docs/CORRECTNESS_ARGUMENT.md`, and `docs/EXTERNAL_REVIEW.md`. These explain how the 0BSD core is aligned with the public Transvoxel outcome requirements while remaining independent from the MIT-licensed official table file.
