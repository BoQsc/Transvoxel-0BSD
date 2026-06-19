# M12 M4 Godot Backend Comparison

M12 compares the default independent transition table and optional M4 candidate table through the same Godot mesh path.

- Status: `PASS_M12_M4_GODOT_BACKEND_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M11 status: `PASS_M11_M4_GODOT_VIEWER_EXPORT_PATH_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Godot project preflight: `PASS`
- Godot runtime executed: `True`
- Backend comparison validation: `PASS_M4_GODOT_BACKEND_COMPARE`

## Comparison

- Same case sequence: `True`
- Same non-empty cell count: `True`
- Default vertices/triangles: `1115` / `1362`
- M4 vertices/triangles: `373` / `245`
- Vertex delta M4-default: `-742`
- Triangle delta M4-default: `-1117`
- M4 structurally distinct: `True`
- Default backend by default: `True`
- M4 requires explicit selection: `True`

## What passed

- both table paths build valid Godot `ArrayMesh` outputs;
- `MeshDataTool` reads both outputs successfully;
- both paths use the same deterministic case sequence;
- M4 output is structurally distinct from the default output;
- M4 remains opt-in and the default backend remains unchanged;

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- finished gameplay terrain integration through Godot/GDExtension;
- decision to make M4 the default backend.
