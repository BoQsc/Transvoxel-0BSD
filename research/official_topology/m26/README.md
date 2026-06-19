# M26 - Godot Voxel Table Integration

M26 tests the MIT-licensed M25 exact data through the table API used by the pinned
local Godot Voxel Transvoxel mesher.

The test does not modify the Godot Voxel checkout. It:

1. copies the pinned `transvoxel_tables.cpp` into a temporary build tree;
2. generates a replacement with the same namespace, structs, accessors, and
   array capacities;
3. compiles the same Godot-style consumer against both files with Zig C++;
4. compares all 256 regular cases, all 512 transition cases, packed reuse
   codes, triangle winding, and transition corner reuse data;
5. builds the complete pinned Godot Voxel Windows GDExtension with Zig in
   temporary clones and records the DLL hash.

The generated exact replacement is MIT because M24 topology-selection rules
were calibrated against the external MIT oracle. M26 test code and aggregate
reports remain 0BSD.

The full compile/link proof does not yet include loading the resulting DLL in a
Godot editor and performing a visual terrain comparison.
