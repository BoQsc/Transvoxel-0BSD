# Godot staged validation project

This folder is a small Godot 4 project for validation and inspection.

The project now uses numbered stage folders instead of a single growing `scripts/` folder:

```text
godot/stages/01_runtime/       runtime/table-load dump
godot/stages/02_mesh_api/      ArrayMesh/MeshDataTool dump
godot/stages/03_seam_metrics/  non-visual seam metrics for the production gate
godot/stages/04_viewer/        optional visual viewer scene
godot/stages/05_m4_candidate_metrics/
                                optional M4 candidate data-path metrics
godot/stages/08_m4_candidate_viewer/
                                optional M4 candidate ArrayMesh viewer/export path
```

The main scene is:

```text
res://stages/04_viewer/TransvoxelValidation.tscn
```

The one-click runner executes the stage scripts automatically. Run from the package root:

```text
RUN.cmd
```

Stage output paths:

```text
godot/validation/01_runtime/runtime_dump.json
godot/validation/02_mesh_api/mesh_api_dump.json
godot/validation/03_seam_metrics/seam_metrics.json
godot/validation/05_m4_candidate_metrics/m4_candidate_metrics.json
godot/validation/08_m4_candidate_viewer/m4_candidate_viewer.json
```

Visual controls for the viewer stage:

```text
1  plane field
2  sphere field
3  tunnel field
4  saddle field
5  wave/noise field
6  edited-plane field
G  toggle case gallery
T  toggle terrain strip
R  rebuild
W  toggle wireframe material
```

Screenshots are not the proof source. The production gate uses JSON metrics.
