# M21 Consumer Compatibility Contract

Status: `PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY`

Functional compatibility: `PROVEN`
Default transition backend: `clean_room_m4_published_topology`
Compiler: `zig cc`

## Contract

- Public C API callers use `tv_build_regular_cell()` and `tv_build_transition_cell()`.
- C++ consumers can include `transvoxel.h` and link a C-compiled object through `extern "C"`.
- The default transition backend is clean-room M4 published-topology behavior.
- `TV_TRANSITION_SAMPLE_COUNT` remains 14 for ABI compatibility; sample 13 is ignored by the default M4 path.
- Callback customization is retained and reset restores the default M4 backend.
- Exact official table layout, class IDs, vertex encoding, and bytes are not claimed.

## Metrics

- Cases: `512`
- Default vertices: `4096`
- Default triangles: `2640`
- Max vertices/case: `12`
- Max triangles/case: `12`
- M4 matches: `512`
- Sample 13 ignored checks: `512`
