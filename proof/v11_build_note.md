# v11 build note

v11 adds the missing Godot-side `seam_metrics.json` generation step.

The one-click runner now executes:

1. Python proof suite.
2. Godot runtime dump.
3. Godot mesh API dump.
4. Godot seam metrics dump.
5. Godot dump validation.
6. Production gate.

The expected production-gate blocker from v10 was `godot/validation/seam_metrics.json`.
