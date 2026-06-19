# Run modes

Use the mode-specific `.cmd` files instead of typing commands.

## Everyday checks

`RUN_FAST.cmd`

Runs the Python table/proof suite and rebuilds the core distribution. It skips the slow C compiler step and Godot seam metrics. This is useful while editing docs, generators, or packaging.

Result status is `FAST_PASS`, not a release proof.

## Core release check

`RUN_CORE.cmd`

Compiles and runs the default C examples, the optional M4 backend package
example, and the optional M4 terrain export example when a compiler is available, then rebuilds
`dist/transvoxel_0bsd_core.zip`.

## Godot validator check

`RUN_GODOT.cmd`

Runs the staged Godot validators and checks the production gate using the latest generated data.

The optional M4 candidate Godot data-path metrics are checked by the Python
proof suite and `RUN_M10.cmd`. `RUN_M11.cmd` additionally requires actual Godot
runtime execution of the M4 viewer/export mesh path.

## Full release proof

`RUN_FULL.cmd` or `RUN.cmd`

Runs everything: Python proof, C core compile, dist build, Godot runtime dump,
Godot mesh dump, seam metrics, optional M4 Godot runtime stages, and production
gate.

Upload only:

```text
proof/SEND_TO_CHATGPT.zip
```

## RUN_AUTO.cmd

Runs the deterministic Godot headless auto-interaction proof. It is for checking scripted dig/add edits without relying on screenshots or human visual judgement.

## Official-topology M4 milestones

```text
RUN_M8.cmd   optional M4 backend package proof
RUN_M9.cmd   optional M4 terrain export proof
RUN_M10.cmd  optional M4 Godot data-path metrics proof
RUN_M11.cmd  optional M4 Godot viewer/export mesh proof
```
