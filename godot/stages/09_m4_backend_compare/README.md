# Stage 09: M4 backend comparison

This stage loads both transition data paths:

```text
res://generated/transition_tables.json
res://generated/official_topology_candidate_tables.json
```

It builds the same deterministic transition-strip-style mesh twice:

- once with the default independent table;
- once with the optional M4 candidate table.

The output is:

```text
godot/validation/09_m4_backend_compare/m4_backend_compare.json
```

This proves a Godot report path can explicitly select and compare the default
backend and the optional M4 candidate backend. It does not make M4 the default
backend and does not prove official `Transvoxel.cpp` equivalence.
