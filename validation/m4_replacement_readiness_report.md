# M4 Replacement Readiness

Status: **READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_EXACT_COMPATIBILITY_BLOCKED**

## Decisions

- Optional M4 transition backend candidate ready: `True`
- Ready to replace the default transition backend: `True`
- Ready to claim a functional full Transvoxel.cpp replacement: `True`
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
- `m4_multi_face_corner_junction_validation`
- `m4_selected_full_production_gate`
- `official_reference_convention_equivalence`
- `official_transition_topology_equivalence`
- `official_vertex_encoding_equivalence`
- `official_triangle_triangulation_identity`
- `official_regular_cell_equivalence`
- `transvoxel_cpp_consumer_compatibility_contract`
- `compatible_transvoxel_cpp_data_layout`
- `unchanged_style_cpp_consumer`

## Blocking evidence

- `official_class_id_mapping`: Official 73 transition-class mapping
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Derive official-compatible class numbering from a no-copy canonical representative ordering.
- `official_regular_table_identity`: Exact official regular-cell class/encoding/table identity
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Do not use official arrays as an oracle. Exact regular table identity is not required for functional replacement.
- `exact_0bsd_provenance_clearance`: 0BSD provenance clearance for oracle-calibrated exact data
  - Actual: `False`
  - Required: `True`
  - Next: Replace oracle-calibrated selections with a defensible independent derivation or obtain explicit provenance/legal clearance before shipping them as 0BSD.
- `official_transvoxel_cpp_byte_identity`: Byte-for-byte identity with the MIT Transvoxel.cpp table file
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN only if exact table-file compatibility is claimed`
  - Next: Do not use official arrays as an oracle. This is not required for a functional clean-room replacement.

## Next milestone

`M26_REAL_ENGINE_INTEGRATION_AND_PROVENANCE` — Replace the MIT table file in a real Transvoxel consumer integration, compare runtime output, and resolve the exact-candidate 0BSD provenance gate.

Byte-for-byte table identity is tracked separately. It is not required for a functional clean-room replacement, but it is required before claiming exact table-file compatibility.
