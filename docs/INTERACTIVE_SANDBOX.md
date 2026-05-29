# Interactive sandbox

The interactive sandbox is the human proof stage. The machine proof gate still decides whether the tables and seam metrics are consistent; this stage lets a person fly through the terrain, edit it, and judge whether the result behaves like usable voxel terrain.

Run it with:

```text
RUN_INTERACTIVE.cmd
```

Controls:

```text
W/A/S/D      move camera
Space/Ctrl   move up/down
Mouse        look around after clicking the window
1..6         switch terrain field
E            dig at camera target
Q            add material at camera target
R            reset edits and rebuild
F            rebuild without clearing edits
T            toggle transition strip
L            toggle reference LOD meshes
O            toggle edit marker spheres
V            toggle wireframe
H            print help
Esc          release mouse
```

The scene writes a small session report to:

```text
godot/validation/06_interactive_sandbox/session.json
```

The report is intentionally small and can be bundled by `proof/SEND_TO_CHATGPT.zip` after a normal run.

Current limitation: this is an evaluation sandbox, not the final production terrain engine. The core product remains the engine-independent 0BSD C core and generated tables.
