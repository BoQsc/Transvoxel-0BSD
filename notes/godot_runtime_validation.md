# Godot runtime validation scope

v7 adds a Godot 4 project that consumes the generated tables in engine code.

It proves these things:

- Godot can load the generated JSON table files.
- Godot can create ArrayMesh surfaces from regular-cell and transition-cell table entries.
- The validation scene can render a gallery of transition cases.
- The validation scene can render a simple high-LOD / transition / low-LOD strip from SDF samples.
- Runtime diagnostics are printed from the same data files shipped by the Python generator.

It does not yet prove production readiness for the final game terrain system:

- It is not a GDExtension implementation.
- It is not GPU/compute-shader meshing.
- It does not yet integrate with chunk streaming, materials, collisions, or edits.
- The Python exhaustive proof suite is still the stronger proof for all table cases.

The next useful step after v7 is a real Godot chunk adapter that uses the same
sampling and table ABI as the final terrain pipeline.


## v8 Godot 4.6 parser fix

The Godot validation scripts now avoid fragile `:=` type inference and use explicit typed variables in validation scripts. This fixes the Godot 4.6 parse error where `denom` could not be inferred in `TransvoxelValidation.gd`. The proof runner also copies canonical generated JSON files into `godot/generated/` before validating the Godot project.
