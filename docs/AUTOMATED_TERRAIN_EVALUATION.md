# Automated terrain evaluation

Human visual judgement is useful only after the terrain resembles a finished game scene. Before textures, lighting, gameplay scale, and camera context are good enough, visual judgement is unreliable. This project therefore treats visual inspection as the last layer, not the first layer.

The expected outcome for this project is not merely "it looked okay once". The expected outcome is a repeatable proof stack:

1. The generated tables are deterministic.
2. The C core compiles and runs.
3. Godot can load the tables and generate validation meshes.
4. Seam metrics show zero seam-open edges.
5. Scripted auto-interaction performs many dig/add edits and every post-edit seam check passes.
6. Human interactive evaluation is used after the automated checks are green.

## Proper pass criteria

The machine-readable pass criteria are:

```text
seam_open_edges = 0
invalid_triangles = 0
degenerate_triangles = 0
auto_interaction.failed_checks = 0
auto_interaction.scripted_edits >= 100
auto_interaction.check_count >= 110
```

## Why auto-interaction exists

The interactive sandbox is useful, but it is easy for a person to misjudge a debug mesh without game-quality terrain materials. The auto-interaction stage gives us a deterministic replacement for “I clicked around and it seemed okay”. It runs scripted edits through multiple fields, multiple origins, and seam-focused edit positions, then writes `godot/validation/07_auto_interaction/auto_interaction.json`.

## What this does not prove

This still does not prove final art quality, final gameplay feel, final performance, or official byte-for-byte identity with Eric Lengyel's MIT Transvoxel tables. It proves that the current 0BSD core and validation pipeline survive deterministic edit stress before human visual evaluation.
