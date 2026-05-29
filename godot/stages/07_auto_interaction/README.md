# Stage 07 - Automated interaction proof

This stage runs without a visible window. It performs deterministic scripted edit sequences across multiple terrain fields and validates the transition strip after every edit.

It is not a replacement for real gameplay testing, but it removes the burden of judging a confusing debug terrain by eye. The expected output is:

```text
status: PASS
failed_checks: 0
seam_open_edges: 0
invalid_triangles: 0
degenerate_triangles: 0
```

Output:

```text
godot/validation/07_auto_interaction/auto_interaction.json
```
