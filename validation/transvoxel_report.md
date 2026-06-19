# Transvoxel table validation

Overall: PASS

Transvoxel schema: `boqsc.transvoxel_tables.v1`
Transvoxel SHA-256: `2abb673609099eb3c456c6b4e235fda700c67feea9fa59fa6df8b3b5ff51416f`
Default transition source: `generated/official_topology_candidate_tables.json`

## regular

- OK: `True`
- Cases: `256`
- Classes: `256`
- Vertex refs: `1536`
- Triangles: `820`
- Max vertices/case: `12`
- Max triangles/case: `5`

## transition_m4_default

- OK: `True`
- Cases: `512`
- Classes: `512`
- Vertex refs: `4096`
- Triangles: `2640`
- Max vertices/case: `12`
- Max triangles/case: `12`

## C header smoke test

- Attempted: `False`
- OK: `None`
- Reason: `no C compiler found`

This proves that the generated table ABI round-trips back to the canonical JSON and can be consumed by a minimal C-style table reader. The default transition table is the clean-room M4 published-topology source. This does not prove byte-for-byte identity with Eric Lengyel's MIT-licensed table file.
