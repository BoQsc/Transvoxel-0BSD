# Stage 10: M4 scripted edit comparison

This stage runs a deterministic, non-visual edit sequence similar to the
interactive sandbox/auto-interaction path. After each scripted edit it builds
the same transition-strip-style case sequence with:

- the default independent transition table;
- the optional M4 candidate table.

The output is:

```text
godot/validation/10_m4_scripted_edit_compare/m4_scripted_edit_compare.json
```

This proves that Godot can compare default and M4 behavior under scripted
terrain changes. It does not make M4 the default backend and does not prove
official `Transvoxel.cpp` equivalence.
