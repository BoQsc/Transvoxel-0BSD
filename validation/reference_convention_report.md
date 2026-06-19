# Published Reference Convention Validation

Status: **PASS_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE**

Published algorithmic reference equivalence: **PROVEN**

## Checks

- PASS - `source_spec_is_published_convention_proof`
- PASS - `same_13_sample_geometry_as_figures_4_8_and_4_16`
- PASS - `same_half_face_corner_correspondence`
- PASS - `negative_values_are_inside_case_bits`
- PASS - `published_case_weights_match_figure_4_17`
- PASS - `local_and_published_indexes_are_bijective_for_all_512_cases`
- PASS - `case_complement_commutes_with_index_mapping`
- PASS - `published_180_degree_nibble_property_holds`
- PASS - `all_d4_sample_transforms_commute_with_index_mapping`
- PASS - `generated_runtime_contract_records_mapping`
- PASS - `six_face_frames_are_orientation_preserving`
- PASS - `all_triangle_components_are_coherent_and_outward`
- PASS - `same_topology_complements_reverse_winding`

## Exhaustive coverage

- Case-index bijection cases: `512`
- D4 transform/index comparisons: `4096`
- Wound triangles: `2640`
- Coherent components: `729`
- Same-topology complement pairs: `143`
- Reverse-wound complement pairs: `143`

This proves the public dissertation convention through an explicit case-index permutation. It does not prove official triangle topology, class IDs, vertex encoding, or table bytes.
