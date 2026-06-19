# Stage layout

v12 stops using one growing Godot `scripts/` folder.

Godot validation is split into stable stage folders:

```text
godot/stages/01_runtime/       engine/runtime/table loading facts
godot/stages/02_mesh_api/      ArrayMesh and MeshDataTool facts
godot/stages/03_seam_metrics/  production-gate seam metrics
godot/stages/04_viewer/        optional visual inspection scene
godot/stages/05_m4_candidate_metrics/
                                optional M4 candidate data-path metrics
godot/stages/08_m4_candidate_viewer/
                                optional M4 candidate ArrayMesh viewer/export path
godot/stages/09_m4_backend_compare/
                                optional default-vs-M4 Godot backend comparison
godot/stages/10_m4_scripted_edit_compare/
                                optional default-vs-M4 scripted edit comparison
```

Output is also staged:

```text
godot/validation/01_runtime/runtime_dump.json
godot/validation/02_mesh_api/mesh_api_dump.json
godot/validation/03_seam_metrics/seam_metrics.json
godot/validation/05_m4_candidate_metrics/m4_candidate_metrics.json
godot/validation/08_m4_candidate_viewer/m4_candidate_viewer.json
godot/validation/09_m4_backend_compare/m4_backend_compare.json
godot/validation/10_m4_scripted_edit_compare/m4_scripted_edit_compare.json
```

Each `RUN.cmd` execution also archives a snapshot under:

```text
runs/run_YYYYMMDD_HHMMSS/
```

Rule for future work: do not mutate an old stage to mean something else. Add a new numbered stage.
