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
- `official_regular_cell_equivalence`
- `transvoxel_cpp_consumer_compatibility_contract`

## Blocking evidence

- `official_class_id_mapping`: Official 73 transition-class mapping
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Derive official-compatible class numbering from a no-copy canonical representative ordering.
- `official_vertex_encoding_equivalence`: Official transition vertex encoding and reuse metadata equivalence
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Define and prove an independently derived vertex-code/cache-reuse encoding contract.
- `official_triangle_triangulation_identity`: Exact official transition interior triangulation identity
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Do not use official arrays as an oracle. This is not required for a functional behavioral replacement.
- `official_regular_table_identity`: Exact official regular-cell class/encoding/table identity
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN`
  - Next: Do not use official arrays as an oracle. Exact regular table identity is not required for functional replacement.
- `official_transvoxel_cpp_byte_identity`: Byte-for-byte identity with the MIT Transvoxel.cpp table file
  - Actual: `NOT_PROVEN`
  - Required: `PROVEN only if exact table-file compatibility is claimed`
  - Next: Do not use official arrays as an oracle. This is not required for a functional clean-room replacement.

## Next milestone

`M23_FUNCTIONAL_RELEASE_HARDENING_NO_LOCAL_ZIP` — Keep the functional replacement evidence green and harden release-facing docs/checks without building a local zip.

Byte-for-byte table identity is tracked separately. It is not required for a functional clean-room replacement, but it is required before claiming exact table-file compatibility.
