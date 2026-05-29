# Stage layout

v12 stops using one growing Godot `scripts/` folder.

Godot validation is split into stable stage folders:

```text
godot/stages/01_runtime/       engine/runtime/table loading facts
godot/stages/02_mesh_api/      ArrayMesh and MeshDataTool facts
godot/stages/03_seam_metrics/  production-gate seam metrics
godot/stages/04_viewer/        optional visual inspection scene
```

Output is also staged:

```text
godot/validation/01_runtime/runtime_dump.json
godot/validation/02_mesh_api/mesh_api_dump.json
godot/validation/03_seam_metrics/seam_metrics.json
```

Each `RUN.cmd` execution also archives a snapshot under:

```text
runs/run_YYYYMMDD_HHMMSS/
```

Rule for future work: do not mutate an old stage to mean something else. Add a new numbered stage.
