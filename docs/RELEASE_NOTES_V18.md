# v18 release notes

Adds the first interactive evaluation sandbox while keeping the engine-independent core and proof gate separate.

New files:

```text
RUN_INTERACTIVE.cmd
godot/stages/06_interactive_sandbox/InteractiveSandbox.tscn
godot/stages/06_interactive_sandbox/InteractiveSandbox.gd
docs/INTERACTIVE_SANDBOX.md
```

The sandbox lets a person fly around, switch procedural fields, dig/add material near the camera target, rebuild, toggle transition/reference meshes, and save a small session report.

The final machine proof is still `RUN_FULL.cmd`. The final human proof is personal evaluation in the sandbox.
