# One-click runner

Use this when you do not want to manually run each command.

## Windows

Double-click:

```text
RUN.cmd
```

It runs:

1. Python proof suite.
2. Godot headless runtime dump.
3. Godot headless mesh API dump.
4. Godot dump validation.
5. Production gate check.

Outputs:

```text
proof/ONE_CLICK_RESULT.txt
proof/one_click_log.txt
proof/one_click_report.json
proof/production_gate.json
```

## If Godot is not found

The runner first checks `GODOT_EXE`, then `godot_path.txt`, then PATH, then common Steam Godot folders.

If auto-detection fails, copy this file:

```text
godot_path.txt.example -> godot_path.txt
```

Then edit `godot_path.txt` so it contains only the full path to your Godot executable.

Example:

```text
C:\Program Files (x86)\Steam\steamapps\common\Godot Engine\Godot_v4.6.2-stable_win64.exe
```

## Python-only check

Double-click:

```text
RUN_NO_GODOT.cmd
```

This skips Godot. It is useful when you only want to verify table generation and Python reports.

## Production gate result

`BLOCKED` is not the same thing as a crash. It means the proof system is still missing required data.

At this stage the expected remaining blocker is usually:

```text
godot/validation/seam_metrics.json
```

That file must be produced by a real LOD0-transition-LOD1 seam assembler. It must report `seam_open_edges = 0`, not total outer open edges.
