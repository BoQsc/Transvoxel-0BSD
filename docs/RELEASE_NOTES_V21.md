# Release Notes v21

v21 strengthens the interactive sandbox as a personal-evaluation tool.

Changes:

- Adds per-edit sandbox seam checks.
- Each dig/add edit now records `seam_after_edit` in `session.json`.
- `session.json` now has top-level `seam_open_edges`, `invalid_triangles`, and `degenerate_triangles` from the current interactive edit stack.
- The report includes `edit_checks[]` so uploaded bundles can show whether each edit kept the sandbox transition strip clean.

Important scope note:

The per-edit sandbox check validates adjacent transition-cell side-face consistency in the interactive strip after the current edit stack. It is an interactive regression check. The full production gate remains `RUN_FULL.cmd`.
