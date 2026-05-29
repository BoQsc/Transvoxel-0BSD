# v22 release notes

v22 adds the first automated interaction proof stage.

New files:

```text
godot/stages/07_auto_interaction/DumpAutoInteraction.gd
godot/stages/07_auto_interaction/README.md
tools/validate_auto_interaction.py
RUN_AUTO.cmd
docs/AUTOMATED_TERRAIN_EVALUATION.md
```

Full proof now includes:

```text
Godot runtime dump
Godot mesh API dump
Godot seam metrics dump
Godot automated interaction proof
Auto interaction validation
Production gate
```

The production gate now requires `godot/validation/07_auto_interaction/auto_interaction.json` and `validation/auto_interaction_report.json`.
