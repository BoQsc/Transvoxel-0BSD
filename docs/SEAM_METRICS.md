# Seam Metrics

`godot/scripts/DumpSeamMetrics.gd` is the headless Godot proof step that writes:

```text
godot/validation/seam_metrics.json
```

It validates the generated transition table inside Godot without relying on screenshots.
The production gate requires:

```json
{
  "seam_open_edges": 0,
  "invalid_triangles": 0,
  "degenerate_triangles": 0,
  "tested_face_directions": 6,
  "tested_fields": 5
}
```

The script tests the transition-cell boundary contract, neighboring transition-cell side faces,
and deterministic chunk-strip fields. It is not a frame-time, streaming, collision, or gameplay certification.
