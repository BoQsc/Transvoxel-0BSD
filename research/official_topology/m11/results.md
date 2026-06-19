# M11 M4 Godot Viewer/Export Path

M11 validates that the M4 candidate table can feed real Godot mesh creation and readback.

- Status: `PASS_M11_M4_GODOT_VIEWER_EXPORT_PATH_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M10 status: `PASS_M10_M4_GODOT_DATA_PATH_METRICS_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Godot project preflight: `PASS`
- Godot runtime executed: `True`
- M4 viewer validation: `PASS_M4_GODOT_VIEWER_EXPORT_PATH`

## Runtime mesh outputs

- Case gallery vertices: `90`
- Case gallery triangles: `54`
- Case gallery MeshDataTool error: `0`
- Terrain strip non-empty cells: `63`
- Terrain strip vertices: `373`
- Terrain strip triangles: `245`
- Terrain strip MeshDataTool error: `0`
- Invalid triangles: `0`
- Degenerate triangles: `0`

## What passed

- the M4 candidate table is available in `godot/generated/`;
- the stage builds real `ArrayMesh` objects from M4 candidate cases;
- `MeshDataTool` can read back the generated M4 gallery and strip meshes;
- the deterministic M4 terrain-strip-style mesh has nonzero cells, vertices, and triangles;
- M4 remains optional and the default backend remains unchanged;

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- finished gameplay terrain integration through Godot/GDExtension;
- decision to make M4 the default backend.
