# Release Notes v26

This release fixes the strict correctness audit timing.

In v25, `tools/prove_tables.py` ran `strict_correctness_audit.py` before the Godot seam and auto-interaction stages created their runtime reports. The final full run could pass `production_gate`, but the bundled `corner_junction_report.json` could still show `NOT_AVAILABLE` for Godot seam/auto evidence.

v26 reruns `strict_correctness_audit.py` after the Godot runtime, seam metrics, and auto-interaction stage in `RUN_FULL.cmd`. The final `SEND_TO_CHATGPT.zip` now reflects the actual full-run evidence.

Expected final report behavior after `RUN_FULL.cmd`:

- `production_gate.status = PASS`
- `strict_correctness_audit.transvoxel_style_proof = PASS`
- `strict_correctness_audit.official_transvoxel_equivalence_proof = NOT_PROVEN`
- `corner_junction_report.status = PASS_PARTIAL_JUNCTION_AUDIT` when seam metrics and auto-interaction are present
- `edited_terrain_all_six_faces_scripted = PASS` when seam metrics and automated scripted edits pass

Still not claimed:

- official 73-class mapping
- exact sign/orientation equivalence with Eric Lengyel's MIT tables
- byte/table identity with `Transvoxel.cpp`
- exhaustive proof for every possible production streaming/corner topology
