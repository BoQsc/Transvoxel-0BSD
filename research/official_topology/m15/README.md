# M15: M4 six-face orientation validation

M15 adds a reusable oriented M4 candidate API and validates it in explicit
right-handed frames for:

```text
+X  -X  +Y  -Y  +Z  -Z
```

The local transition-cell contract is:

- `u` and `v` span the 3x3 full-resolution sample face at `w=0`;
- `+w` points toward the four half-resolution samples at `w=1`;
- every built-in face frame has determinant `+1`;
- a negative caller scale is handled by determinant-aware winding correction.

The Zig-compiled C test and actual Godot runtime stage both validate all 512
cases in every frame, transformed triangle orientation, nondegeneracy,
`ArrayMesh`/`MeshDataTool` output in Godot, and deterministic neighboring-cell
side seams.

Run:

```text
RUN_M15.cmd
```

This is an internal six-face consistency proof. It does not prove official
reference convention or official topology equivalence.
