# Canonical table schema

This repository keeps one canonical generated representation and exports other formats from it.

## Canonical JSON files

- `generated/regular_tables.json`
- `generated/transition_tables.json`

Each case contains:

```text
case: integer case index
inside_samples: list of sample indices whose bit is set
vertices: generated edge-intersection vertices
triangles: generated triangle index triples into that case's local vertex list
```

A vertex is stored as the pair of sample indices forming the sign-changing edge:

```json
{"id": 0, "samples": [0, 1]}
```

A triangle is stored as local vertex IDs:

```json
{"vertices": [0, 1, 2]}
```

## Export rule

Exported files must be generated from the canonical JSON. They must not manually edit table values, copy values from external table sources, or use Eric Lengyel's MIT-licensed `Transvoxel.cpp` as input.

The current table ABI uses this lookup chain:

```text
case index -> class index -> class data -> vertex refs + triangles
```

For now, each case maps to its own class. This is intentionally simple and is not the official 73-class compression.
