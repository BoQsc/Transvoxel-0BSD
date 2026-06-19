# M4 candidate metrics stage

This headless stage validates the optional M4 official-topology candidate table
inside the Godot project data layout.

Input:

```text
res://generated/official_topology_candidate_tables.json
```

Output:

```text
res://validation/05_m4_candidate_metrics/m4_candidate_metrics.json
```

It checks table counts, triangle indices/degenerates, and deterministic
neighboring-strip side-face fingerprints. It does not claim official
`Transvoxel.cpp` equivalence.
