# v28 release notes

Fixes the external alignment report ordering/data-shape bug found in v27.

v27 correctly generated `validation/auto_interaction_report.json`, but
`tools/external_alignment_report.py` looked for `failed_checks` and
`scripted_edits` at the top level. The validator actually stores them under
`summary`, so the final post-gate external alignment step could fail even when:

- production gate passed,
- Godot seam metrics passed,
- auto-interaction passed,
- strict correctness audit passed.

v28 reads both supported shapes:

- `validation/auto_interaction_report.json`
- `godot/validation/07_auto_interaction/auto_interaction.json`

No core geometry, generated tables, or proof thresholds changed.
