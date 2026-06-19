# Known Limits

This project currently proves a working independent Transvoxel-style transition system. It does not prove every possible stronger claim.

Still not claimed:

```text
Official 73-equivalence-class mapping is not proven.
Exact sign/orientation convention equivalence with Eric Lengyel's MIT table file is not proven.
Exact topology identity with the official table file is not proven.
The optional M4 candidate backend is package-tested, but official equivalence is still not proven.
The optional M4 terrain export path is C-tested, but full Godot gameplay/GDExtension terrain integration through M4 is still not proven.
The optional M4 Godot data path is staged and Python-metrics validated; `RUN_M10.cmd` executes the M4 Godot stage only when Godot is available locally.
The optional M4 Godot viewer/export mesh path is validated by `RUN_M11.cmd` only when Godot is available locally.
The optional default-vs-M4 Godot comparison path is validated by `RUN_M12.cmd` only when Godot is available locally.
The optional default-vs-M4 Godot scripted edit comparison path is validated by `RUN_M13.cmd` only when Godot is available locally.
The M4 all-six-face orientation path is validated in Zig C and actual Godot runtime evidence by `RUN_M15.cmd`.
The M4 replacement-readiness gate still blocks default/full replacement because M4 junction proof, M4-selected production proof, official reference/topology behavior, regular-cell equivalence, and consumer compatibility are not all proven.
Game-ready art/texture/lighting quality is not certified.
Gameplay performance in a complete streaming world is not certified.
```

Current proof covers the independent core:

```text
512 transition cases covered by generated-table proof.
No seam cracks in the scripted Godot validation gate.
No failed checks in automated scripted edit tests when RUN_FULL passes.
C core builds and runs when a compiler is available.
Optional M4 candidate backend builds and runs through the normal C API when a compiler is available.
Optional M4 candidate backend builds the C terrain export path when a compiler is available.
Optional M4 candidate table is synced into `godot/generated/` and passes Godot-style table metrics.
Optional M4 candidate table can build real Godot ArrayMesh data and pass MeshDataTool readback when RUN_M11 runs with Godot.
Default and M4 Godot transition-strip mesh outputs can be compared side by side when RUN_M12 runs with Godot.
Default and M4 Godot transition-strip mesh outputs can be compared after scripted edits when RUN_M13 runs with Godot.
M4 candidate cells and deterministic neighbor seams pass across explicit +X/-X/+Y/-Y/+Z/-Z frames in Zig C and Godot.
Small public dist package is generated and checked.
```
