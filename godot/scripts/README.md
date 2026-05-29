# Legacy location intentionally empty

Godot validation scripts are split by stage under `res://stages/`.

- `res://stages/01_runtime/DumpRuntimeData.gd`
- `res://stages/02_mesh_api/DumpMeshData.gd`
- `res://stages/03_seam_metrics/DumpSeamMetrics.gd`
- `res://stages/04_viewer/TransvoxelValidation.tscn`

This avoids the old single `scripts/` folder becoming a pile of unrelated tests.
