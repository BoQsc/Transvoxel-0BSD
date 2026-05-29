# Reporting interactive sandbox results

Use this when you are doing the personal human evaluation step.

1. Run `RUN_INTERACTIVE.cmd`.
2. Walk around, switch fields, dig/add terrain, and close the Godot window.
3. Upload `proof/SEND_TO_CHATGPT.zip`.

The upload bundle includes `godot/validation/06_interactive_sandbox/session.json` only if the sandbox wrote it. A normal `RUN_FULL.cmd` proof run does not prove personal interaction; it proves the machine regression gate.


## v20 note

`RUN_INTERACTIVE.cmd` now creates a self-contained session report by running a seam metrics precheck before opening the sandbox. Upload `proof/SEND_TO_CHATGPT.zip` after closing the sandbox.

## v21 per-edit checks

After v21, each dig/add operation records a `seam_after_edit` object in `godot/validation/06_interactive_sandbox/session.json`.

The useful fields are:

```text
edit_checks[].seam_after_edit.status
edit_checks[].seam_after_edit.seam_open_edges
edit_checks[].seam_after_edit.invalid_triangles
edit_checks[].seam_after_edit.degenerate_triangles
```

For a clean interactive edit session, every `seam_after_edit.status` should be `PASS` and `seam_open_edges` should be `0`.
