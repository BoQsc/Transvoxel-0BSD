# Release notes v20

Interactive sandbox reporting cleanup.

Changes:

- `RUN_INTERACTIVE.cmd` now runs the seam-metrics headless precheck before opening the sandbox, so the interactive session can reference current machine seam metrics.
- The sandbox no longer spams errors when optional seam metrics are missing.
- Removed the invalid Godot 4.6 per-material `wireframe` assignment that caused `SpatialMaterial remapped parameter not found: wireframe` warnings.
- `session.json` now records `dig_count`, `add_count`, and `INTERACTIVE_SESSION_WRITTEN` status.

This still does not make the interactive run a production gate. Use `RUN_FULL.cmd` for the full machine proof.
