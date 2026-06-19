# M13 M4 Godot Scripted Edit Comparison

M13 compares the default independent transition table and optional M4 candidate table under deterministic scripted Godot edits.

- Status: `PASS_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M12 status: `PASS_M12_M4_GODOT_BACKEND_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Godot project preflight: `PASS`
- Godot runtime executed: `True`
- Scripted edit comparison validation: `PASS_M4_GODOT_SCRIPTED_EDIT_COMPARE`

## Scripted edit comparison

- Scenarios: `14`
- Scripted edits: `112`
- Checks: `126`
- Failed checks: `0`
- Edited checks with changed case sequence: `104`
- Scenarios with changes: `14`
- Structurally distinct checks: `126`
- Default total triangles: `22566`
- M4 total triangles: `4303`
- Triangle delta M4-default: `-18263`
- Default backend by default: `True`
- M4 requires explicit selection: `True`

## What passed

- both table paths build valid Godot `ArrayMesh` outputs after every scripted edit;
- `MeshDataTool` reads both backend outputs successfully;
- scripted edits actually changed transition case sequences in every scenario;
- M4 output remains structurally distinct from the default output;
- M4 remains opt-in and the default backend remains unchanged;

## What remains unproven

- official Transvoxel.cpp byte/table identity;
- official class ID mapping;
- official triangle topology equivalence;
- finished gameplay terrain integration through Godot/GDExtension;
- decision to make M4 the default backend.
