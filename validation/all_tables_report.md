# All Table Validation Report

This validates only the clean-room generators in this repository. It does not compare against or copy Eric Lengyel's MIT-licensed Transvoxel.cpp table values.

Overall OK: `True`

## regular

- OK: `True`
- Schema: `boqsc.regular_tables.v1`
- Status: `clean_room_modified_marching_cubes_preferred_polarity`
- SHA-256: `fb749cd25ee3ee77be38f1b6d12e0a26e2f5817c8ee246d1b30e5b9cc73f2a15`
- Cases: `256`
- Non-empty cases: `254`
- Empty cases: `2`
- Vertices per case: `0` .. `12`
- Triangles per case: `0` .. `5`
- Total vertex-pairs across cases: `1536`
- Total triangles across cases: `820`

## transition

- OK: `True`
- Schema: `boqsc.transition_tables.v1`
- Status: `experimental_not_drop_in_transvoxel_cpp`
- SHA-256: `db8d6c36ca74d014afa8a78303db2b746b523a8223dd89c250230ff3a9eb21c0`
- Cases: `512`
- Non-empty cases: `510`
- Empty cases: `2`
- Vertices per case: `0` .. `28`
- Triangles per case: `0` .. `36`
- Total vertex-pairs across cases: `10496`
- Total triangles across cases: `12288`

## Meaning

These checks prove deterministic generation and structural sanity for the local 0BSD tables. They do not prove that the tables are equivalent to official Transvoxel lookup tables or production-ready for every terrain edit.
