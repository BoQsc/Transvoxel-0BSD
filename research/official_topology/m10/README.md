# M10 M4 Godot Data-Path Metrics

M10 adds a Godot-stage-compatible data path for the optional M4 candidate
backend.

It adds:

- `godot/generated/official_topology_candidate_tables.json`
- `godot/stages/05_m4_candidate_metrics/DumpM4CandidateMetrics.gd`
- `tools/validate_m4_godot_candidate.py`

The local M10 proof syncs the M4 table into the Godot project, verifies the
Godot project preflight, runs the Python validator with the same metrics shape
as the Godot stage, and executes the Godot stage when a Godot executable is
available.

M10 does not prove official `Transvoxel.cpp` equivalence.

Run:

```text
RUN_M10.cmd
```
