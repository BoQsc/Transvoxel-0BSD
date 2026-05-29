# Transvoxel table validation

Overall: PASS

Transvoxel schema: `boqsc.transvoxel_tables.v1`
Transvoxel SHA-256: `245447e0c377138bd01c16f60a49c9b7e726556b9efcf3e5c384efb15a9aefd0`

## regular

- OK: `True`
- Cases: `256`
- Classes: `256`
- Vertex refs: `2432`
- Triangles: `1920`
- Max vertices/case: `13`
- Max triangles/case: `12`

## transition

- OK: `True`
- Cases: `512`
- Classes: `512`
- Vertex refs: `10496`
- Triangles: `12288`
- Max vertices/case: `28`
- Max triangles/case: `36`

## C header smoke test

- Attempted: `True`
- OK: `True`
- Compiler: `/usr/bin/cc`
- Output: `regular=1920 transition=12288`

This proves that the generated table ABI round-trips back to the canonical JSON and can be consumed by a minimal C-style table reader. It does not prove byte-for-byte identity with Eric Lengyel's MIT-licensed table file.
