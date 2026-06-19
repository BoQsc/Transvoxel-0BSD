# M21 Default M4 Functional Consumer Compatibility

M21 switches the public default transition export to the clean-room M4 published-topology table and proves the functional C/C++ consumer contract.

- Status: `PASS_M21_DEFAULT_M4_FUNCTIONAL_CONSUMER_COMPATIBILITY`
- Transvoxel export validation: `True`
- Core C examples: `PASS`
- M4 callback adapter package: `PASS_M4_BACKEND_PACKAGE_C_EXAMPLE`
- Terrain default/adapter export: `PASS_M4_TERRAIN_NORMAL_API_EXPORT`
- Consumer compatibility: `PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY`
- Readiness: `READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_EXACT_COMPATIBILITY_BLOCKED`
- Godot runtime executed: `True`

## Default transition metrics

- Cases: `512`
- Vertices / triangles: `4096` / `2640`
- Max vertices / triangles: `12` / `12`
- M4 direct matches: `512`
- Sample 13 ignored checks: `512`

## Claim boundary

- Allowed now: Functional clean-room Transvoxel.cpp replacement through the public C/C++ API: default regular and transition builders use clean-room published behavior; C and C++ consumers can compile/link; callback customization is retained.
- Not allowed now: Exact official Transvoxel.cpp table layout, class-ID, vertex encoding, triangulation-identity, or byte-identity claim.

No zip/package artifact is built by this milestone runner.
