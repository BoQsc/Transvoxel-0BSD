# M18 Published Reference-Convention Validation

M18 proves M4's published sample/sign/case-index/face/winding convention through an explicit no-copy bijection.

- Status: `PASS_M18_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE`
- Python convention proof: `PASS_PUBLISHED_REFERENCE_CONVENTION_EQUIVALENCE`
- Zig C API proof: `PASS_M18_ZIG_PUBLISHED_REFERENCE_CONVENTION_API`
- Readiness reference gate: `PASS`

## Exhaustive coverage

- Case mappings: `512`
- Distinct published indexes: `512`
- D4 mapping comparisons: `4096`
- Six-face frames: `6`
- Wound triangles: `2640`
- Coherent components: `729`
- Same-topology complement pairs: `143`
- Reverse-wound complement pairs: `143`

## Readiness effect

- Remaining blocking gates: `6`
- Next milestone: `M19_OFFICIAL_TRANSITION_TOPOLOGY_VALIDATION`

M18 proves the published algorithmic reference convention. Official transition triangulation topology, class IDs, vertex encoding, regular-cell equivalence, consumer compatibility, and table bytes remain separate.
