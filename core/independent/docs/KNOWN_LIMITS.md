# Known Limits

M21 makes the public C/C++ API ready as a functional clean-room Transvoxel.cpp replacement: default regular cells use the M20 clean-room table, default transition cells use the M21 clean-room M4 published-topology table, and the consumer compatibility contract is tested.

M22 locks the exact-compatibility claim boundary. The functional replacement
claim is allowed; exact official compatibility claims remain blocked.

M23 confirms those exact gaps by comparing all cases with a verified external
oracle. The current implementation is not yet an exact drop-in replacement.
Exact replacement is the active finish line, and M24 targets topology
convergence before field/symbol compatibility and unchanged-consumer tests.

Still not claimed:

```text
Official 73-equivalence-class ID mapping is not proven.
Official vertex/reuse encoding equivalence is not proven.
Exact official transition triangulation identity is not proven.
Exact official regular table identity is not proven.
Byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp table file is not proven.
Full Godot gameplay/GDExtension terrain integration is not proven.
Game-ready art/texture/lighting quality is not certified.
Gameplay performance in a complete streaming world is not certified.
Collision, streaming, materials, and engine policy are outside this small core.
```

Current proof covers:

```text
M18 published reference convention and 512-case index bijection.
M19 published transition topology behavior for all 512 transition cases.
M20 default clean-room regular-cell table replacement.
M21 default clean-room M4 transition table replacement.
M21 C/C++ consumer compatibility through the public API.
M22 exact compatibility claim-boundary validation.
Public transition ABI keeps 14 samples; sample 13 is ignored by the default M4 path.
Default transition table totals: 512 cases, 4096 vertex refs, 2640 triangles, max 12 vertices and 12 triangles.
Default regular table totals: 256 cases, 1536 vertex refs, 820 triangles, max 12 vertices and 5 triangles.
M4 direct/oriented/mapped APIs remain available for explicit face-frame and edge/corner calls.
Callback customization remains available and reset restores the default M4 backend.
Actual Godot runtime dump validates the default transvoxel export when RUN_M21 runs with Godot available.
```

Byte identity is not required for the functional replacement claim, but it is required before claiming exact official table-file compatibility.
