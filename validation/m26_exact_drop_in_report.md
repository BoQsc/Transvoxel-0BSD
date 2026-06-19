# M26 Exact Drop-in Integration

Status: `PASS_M26_EXACT_DROP_IN_INTEGRATION_PROVEN_PROVENANCE_BLOCKED`

- Godot Voxel table API integration: `PASS_M26_GODOT_VOXEL_TABLE_INTEGRATION`
- Regular cases: `256/256`
- Transition cases: `512/512`
- Transition corner records: `13/13`
- Mismatches: `0`
- Full Godot Voxel GDExtension build: `PASS_M26_FULL_GODOT_VOXEL_GDEXTENSION_BUILD`
- Built DLL bytes: `8256512`
- Exact semantic drop-in integration ready: `True`
- Exact semantic drop-in 0BSD release ready: `False`
- Drop-in release blockers: `exact_0bsd_provenance_clearance`
- Identity-only blockers: `official_class_id_mapping, official_regular_table_identity, official_transvoxel_cpp_byte_identity`
- Next milestone: `M27_INDEPENDENT_EXACT_TOPOLOGY_PROVENANCE`

M26 proves exact semantic replacement through the pinned Godot Voxel table-source API and a full Zig GDExtension compile/link. The candidate remains research-only because M24 triangulation option indexes were calibrated by the MIT oracle.

No zip artifact is built.
