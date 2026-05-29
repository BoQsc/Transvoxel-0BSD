# Reporting back

After running `RUN.cmd`, upload only this file when asking for help:

```text
proof/SEND_TO_CHATGPT.zip
```

That zip contains the useful result files:

- `proof/ONE_CLICK_RESULT.txt`
- `proof/one_click_log.txt`
- `proof/one_click_report.json`
- `proof/production_gate.json`
- `proof/proof_dump.json`
- `validation/*.json` reports needed for diagnosis
- `godot/validation/01_runtime/runtime_dump.json`
- `godot/validation/02_mesh_api/mesh_api_dump.json`
- `godot/validation/03_seam_metrics/seam_metrics.json`
- failure OBJ diagnostics if any are generated

The runner also copies the same upload zip into the timestamped run folder:

```text
runs/run_YYYYMMDD_HHMMSS/SEND_TO_CHATGPT.zip
```

Do not paste the console output unless the runner itself crashes before writing the zip.
