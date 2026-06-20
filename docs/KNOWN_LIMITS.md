# Known Limits

## Production trust boundary

The 0BSD core is usable, but it should not be presented as having the same
production risk as the official upstream MIT implementation. Start production
with upstream `Transvoxel.cpp` behind a stable adapter, establish a long-term
baseline, and move to 0BSD only after equivalent engine-level qualification.
Choose 0BSD earlier only when independent provenance is a hard requirement.

The independent path matches vertex counts, triangle counts, crossing-edge
vertex sets, and tested seam boundaries for every case. Exact oriented
interior topology matches only 86/256 regular and 139/512 transition cases.
Different valid interiors can change local normals, lighting, interpolation,
collision triangles, and contact response even when seams remain closed.

See `docs/CHOOSING_0BSD_OR_MIT.md` for the full decision boundary.

M21 makes the public C/C++ API ready as a functional clean-room Transvoxel.cpp replacement: default regular cells use the M20 clean-room table, default transition cells use the M21 clean-room M4 published-topology table, and the consumer compatibility contract is tested.

M22 locks the exact-compatibility claim boundary. The functional replacement
claim is allowed; exact official compatibility claims remain blocked.

M23 confirms the exact gaps by comparing all cases with a verified external
oracle. M24-M26 then prove a technically exact research candidate, including
field/symbol compatibility and downstream integration.

M24 reaches exact edge-labeled oriented topology for all 768 cases in an
isolated research candidate. It does not yet reproduce official vertex order,
reuse/cache metadata, class/table layout, or the unchanged `Transvoxel.cpp`
consumer surface. The public default therefore remains the functional M21
table.

The M24-M26 exact selection-bearing artifacts are MIT. Their generator code and
aggregate reports are 0BSD, and the public 0BSD core excludes the MIT files.

M25's generated `Transvoxel.cpp` preserves the original data contract but uses
independent internal class IDs.

M26 compiles the actual pinned Godot Voxel table-source API against the M25
candidate and matches all 781 exhaustive output records. It also compiles and
links the complete pinned Windows GDExtension with Zig against a local Godot
4.5 `godot-cpp` dependency. Runtime editor loading and visual terrain
comparison for this exact candidate are not yet performed. The exact generated
data is explicitly MIT.

M27 is the terminal exact-0BSD decision. The independent deterministic rule
matches exact oriented topology in 86/256 regular and 139/512 transition cases.
Published rules constrain robust boundaries but permit multiple legal
interiors. The exact M24-M26 candidate closes those gaps with
MIT-oracle-calibrated selections, so those files are MIT rather than 0BSD.
There is no automatic M28.

Still not claimed:

```text
Official 73-equivalence-class ID mapping is not proven.
Official numeric 73-class ID identity is not proven.
Exact official regular table byte/class identity is not proven.
Byte-for-byte identity with Eric Lengyel's MIT Transvoxel.cpp table file is not proven.
0BSD provenance clearance for the M24-M26 exact candidate is not proven; M27 records the exact 0BSD goal as terminally not achieved.
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
M24 exact oriented topology for all 768 cases in the research candidate.
M25 compatible packed reuse semantics and original data ABI.
M26 pinned Godot Voxel table-source integration: 781/781 records match.
M26 full Windows GDExtension compile/link with Zig: PASS.
M27 terminal provenance audit: exact 0BSD goal NOT_ACHIEVED.
Public transition ABI keeps 14 samples; sample 13 is ignored by the default M4 path.
Default transition table totals: 512 cases, 4096 vertex refs, 2640 triangles, max 12 vertices and 12 triangles.
Default regular table totals: 256 cases, 1536 vertex refs, 820 triangles, max 12 vertices and 5 triangles.
M4 direct/oriented/mapped APIs remain available for explicit face-frame and edge/corner calls.
Callback customization remains available and reset restores the default M4 backend.
Actual Godot runtime dump validates the default transvoxel export when RUN_M21 runs with Godot available.
```

Byte identity is not required for the functional replacement claim, but it is required before claiming exact official table-file compatibility.
