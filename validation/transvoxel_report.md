# Transvoxel table validation

Overall: PASS

Transvoxel schema: `boqsc.transvoxel_tables.v1`
Transvoxel SHA-256: `308f84d257294f03adeb35651d60bc905bf0d8b12c1cdedb9bdf089bcc325b14`

## regular

- OK: `True`
- Cases: `256`
- Classes: `256`
- Vertex refs: `1536`
- Triangles: `820`
- Max vertices/case: `12`
- Max triangles/case: `5`

## transition

- OK: `True`
- Cases: `512`
- Classes: `512`
- Vertex refs: `10496`
- Triangles: `12288`
- Max vertices/case: `28`
- Max triangles/case: `36`

## C header smoke test

- Attempted: `False`
- OK: `None`
- Reason: `no C compiler found`

This proves that the generated table ABI round-trips back to the canonical JSON and can be consumed by a minimal C-style table reader. It does not prove byte-for-byte identity with Eric Lengyel's MIT-licensed table file.
