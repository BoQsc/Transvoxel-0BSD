# M14 M4 Replacement-Readiness Gate

M14 makes the default/full-replacement decision explicit from current machine-readable evidence.

- Status: `PASS_M14_REPLACEMENT_READINESS_GATE_BLOCKED_ON_REQUIRED_EVIDENCE`
- M13 status: `PASS_M13_M4_GODOT_SCRIPTED_EDIT_COMPARE_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- Readiness report: `BLOCKED_M4_DEFAULT_REPLACEMENT_REQUIRED_EVIDENCE_NOT_PROVEN`

## Decisions

- Optional M4 transition backend candidate ready: `True`
- Ready to replace default transition backend: `False`
- Functional full replacement ready: `False`
- Exact table-compatible replacement ready: `False`

## Blocking gates

- `m4_all_six_face_orientation_runtime_validation`
- `m4_multi_face_corner_junction_validation`
- `m4_selected_full_production_gate`
- `official_reference_convention_equivalence`
- `official_transition_topology_equivalence`
- `official_class_id_mapping`
- `official_vertex_encoding_equivalence`
- `official_regular_cell_equivalence`
- `transvoxel_cpp_consumer_compatibility_contract`
- `official_transvoxel_cpp_byte_identity`

## Next milestone

- ID: `M15_M4_SIX_FACE_ORIENTATION_VALIDATION`
- Objective: Prove M4 runtime geometry and seams across all six transition-face orientations using explicit sample/vertex frame transforms in C and Godot.
- Reason: This is the nearest self-contained blocker to making M4 the default and creates the orientation machinery required for later official-reference and corner-junction proofs.

M14 passing means the decision gate is correct and honest. It does not mean the replacement itself is proven.
