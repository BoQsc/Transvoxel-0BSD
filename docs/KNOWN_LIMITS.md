# Known Limits

This project currently proves a working independent Transvoxel-style transition system. It does not prove every possible stronger claim.

Still not claimed:

```text
Official 73-equivalence-class mapping is not proven.
Exact sign/orientation convention equivalence with Eric Lengyel's MIT table file is not proven.
Exact topology identity with the official table file is not proven.
The optional M4 candidate backend is package-tested, but official equivalence is still not proven.
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
Small public dist package is generated and checked.
```
