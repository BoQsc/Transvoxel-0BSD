# Validation Report

This report validates the clean-room generator output. It does not compare against or copy any MIT-licensed Transvoxel.cpp table values.

- OK: `True`
- SHA-256: `db8d6c36ca74d014afa8a78303db2b746b523a8223dd89c250230ff3a9eb21c0`
- Cases: `512`
- Non-empty cases: `510`
- Empty cases: `2`
- Vertices per case: `0` .. `28`
- Triangles per case: `0` .. `36`
- Total generated vertex-pairs across all cases: `10496`
- Total generated triangles across all cases: `12288`

## What this proves

The generated table is deterministic, structurally valid by the repository's own invariants, and all emitted interpolated vertices lie on sign-changing sample edges.

## What this does not prove

This does not prove compatibility with Eric Lengyel's official Transvoxel tables, and it does not prove production-quality triangle patterns for every possible terrain edit. Visual and engine-side seam tests are still required.
