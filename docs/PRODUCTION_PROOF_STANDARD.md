# Production Proof Standard

This project must not use screenshots as proof before machine-readable seam data exists.

## Hard gate

A production proof is blocked until these files exist and pass:

```text
validation/proof_report.json
godot/validation/runtime_dump.json
godot/validation/mesh_api_dump.json
godot/validation/seam_metrics.json
proof/production_gate.json
```

The final gate must say:

```json
{
  "status": "PASS"
}
```

## Required seam numbers

`godot/validation/seam_metrics.json` must include at least:

```json
{
  "seam_open_edges": 0,
  "invalid_triangles": 0,
  "degenerate_triangles": 0,
  "tested_face_directions": 6,
  "tested_fields": 5
}
```

`open_edges_total` is not enough. Finite meshes naturally have outer open edges. The only production-relevant number is whether the LOD seam has open edges.

## Required field tests

Minimum fields:

```text
plane
axis-aligned slope
diagonal slope
sphere/circle cross-section
cave/tunnel
noise/random deterministic field
edited seam field
```

## Required directions

All six chunk face directions must be tested:

```text
+x
-x
+y
-y
+z
-z
```

## Stop rule

If the real seam assembler cannot produce `seam_open_edges = 0`, stop making visualization versions. Fix the topology/generator/assembler first.
