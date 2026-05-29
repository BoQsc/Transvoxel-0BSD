# v10 build note

v10 adds a single-click runner:

- `RUN.cmd` for Windows.
- `RUN_NO_GODOT.cmd` for Python-only checks.
- `run.sh` for Linux/macOS shells.
- `tools/run_everything.py` as the cross-platform orchestrator.

The runner writes:

- `proof/ONE_CLICK_RESULT.txt`
- `proof/one_click_log.txt`
- `proof/one_click_report.json`
- `proof/production_gate.json`

The production gate can still be `BLOCKED` until `godot/validation/seam_metrics.json` exists.
