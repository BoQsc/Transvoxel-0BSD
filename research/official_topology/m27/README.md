# M27 - Terminal Exact-0BSD Decision

M27 is the final roadmap milestone for the exact 0BSD replacement goal. It is
not another release-hardening pass.

The runner regenerates the independent regular and transition topology,
compares every one of the 768 cases with the verified official oracle,
revalidates the exact research candidate through the pinned Godot Voxel table
API and full Zig GDExtension build, and audits the published topology rules and
MIT provenance boundary.

The official dissertation must match SHA-256
`c1c86dc1c441fa86dbe6b4b38a521ffb26a5eec3c4eede0f5782508a6ad41160`.
Set `TRANSVOXEL_DISSERTATION` if it is not in the recorded temporary reference
location. Set `TRANSVOXEL_ORACLE_REPO` if the verified official checkout is in
a different location.

The expected terminal result is successful as an audit even though the exact
0BSD goal is not achieved. The technically exact M24-M26 candidate remains
research-only; the independently derived functional 0BSD core remains usable.

There is no M28. A future review requires an external state change: explicit
permission/relicensing, or a changed project requirement.
