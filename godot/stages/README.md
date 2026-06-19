# Godot stages

Each validation step has its own folder. New work should add a new numbered stage instead of mutating an older stage in-place.

- `01_runtime/` records engine/runtime/table-load facts.
- `02_mesh_api/` records Godot ArrayMesh/MeshDataTool behavior.
- `03_seam_metrics/` records non-visual seam metrics used by the production gate.
- `04_viewer/` is only for human visual inspection after metrics pass.
- `05_m4_candidate_metrics/` records non-visual metrics for the optional M4
  official-topology candidate data path.

Rule: proof comes from JSON metrics first; screenshots are secondary.

## 06_interactive_sandbox

Human evaluation sandbox. It is not part of the production gate. Run it with `RUN_INTERACTIVE.cmd` from the repository root.
