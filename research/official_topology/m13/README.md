# M13 M4 Godot Scripted Edit Comparison

M13 validates a scripted edit comparison path for the default independent
transition table and the optional M4 candidate table inside Godot.

It adds:

```text
godot/stages/10_m4_scripted_edit_compare/DumpM4ScriptedEditCompare.gd
tools/validate_m4_godot_scripted_edit_compare.py
RUN_M13.cmd
```

The stage runs deterministic dig/add edits over multiple fields and origins,
then builds both selected transition-strip-style mesh outputs after every edit.

M4 remains opt-in. This does not prove official `Transvoxel.cpp` equivalence and
does not make M4 the default backend.
