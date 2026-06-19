# M4 Replacement Readiness

Status: **BLOCKED_M4_DEFAULT_REPLACEMENT_REQUIRED_EVIDENCE_NOT_PROVEN**

## Decisions

- Optional M4 transition backend candidate ready: `True`
- Ready to replace the default transition backend: `False`
- Ready to claim a functional full Transvoxel.cpp replacement: `False`
- Ready to claim exact table/encoding compatibility: `False`

## Passing evidence

- `m4_runtime_tables`
- `m5_c_runtime`
- `m6_c_seams`
- `m7_normal_api`
- `m8_package`
- `m9_terrain_export`
- `m10_godot_metrics`
- `m11_godot_viewer`
- `m12_backend_compare`
- `m13_scripted_edits`
- `m4_all_six_face_orientation_runtime_validation`

## Blocking evidence

- `m4_multi_face_corner_junction_validation`: M4-selected corner and multi-neighbor LOD junction proof
  - Actual: `MISSING_M4_SELECTED_JUNCTION_EVIDENCE`
  - Required: `PASS M4-specific corner/junction report`
  - Next: After six-face orientation proof, assemble and validate M4 multi-face corner junctions.
- `m4_selected_full_production_gate`: Full production gate with M4 installed through the normal backend API
  - Actual: `MISSING_M4_PRODUCTION_GATE`
  - Required: `PASS M4-selected runtime, mesh, six-face seams, scripted edits, and production gate`
  - Next: Run the complete production assembler/gate with M4 explicitly installed after orientation and junction validation.
- `official_reference_convention_equivalence`: Official sign, sample-order, face-frame, winding, and orientation convention equivalence
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Derive a no-copy reference transform specification and prove all transition orientations against it.
- `official_transition_topology_equivalence`: Official transition triangulation/topology equivalence for all 512 cases
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Prove the independently derived ambiguity resolutions and triangle topology match the published algorithmic topology.
- `official_class_id_mapping`: Official 73 transition-class mapping
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Derive official-compatible class numbering from a no-copy canonical representative ordering.
- `official_vertex_encoding_equivalence`: Official transition vertex encoding and reuse metadata equivalence
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Define and prove an independently derived vertex-code/cache-reuse encoding contract.
- `official_regular_cell_equivalence`: Official regular-cell topology/reference behavior for a full Transvoxel.cpp replacement
  - Actual: `MISSING_OFFICIAL_REGULAR_CELL_CANDIDATE`
  - Required: `Proven clean-room regular-cell topology/reference behavior`
  - Next: Create a separate no-copy regular-cell equivalence track after the transition orientation gate is established.
- `transvoxel_cpp_consumer_compatibility_contract`: Documented and tested compatibility contract for Transvoxel.cpp consumers
  - Actual: `NOT_CLAIMED`
  - Required: `Explicit adapter/compatibility contract with compile and behavior tests`
  - Next: Specify whether the final product is behavioral replacement, source adapter, or table-layout compatible, then test that contract.
- `official_transvoxel_cpp_byte_identity`: Byte-for-byte identity with the MIT Transvoxel.cpp table file
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN only if exact table-file compatibility is claimed`
  - Next: Do not use official arrays as an oracle. This is not required for a functional clean-room replacement.

## Next milestone

`M16_M4_MULTI_FACE_CORNER_JUNCTION_VALIDATION` — Assemble M4-selected transition meshes on multiple perpendicular LOD faces and prove shared-edge/corner closure in C and Godot.

Byte-for-byte table identity is tracked separately. It is not required for a functional clean-room replacement, but it is required before claiming exact table-file compatibility.
