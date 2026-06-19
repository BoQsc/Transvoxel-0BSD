# M8 M4 Backend Package Proof

M8 promotes the selectable M4 candidate backend from a research-only compile
path into a package-validated optional source path.

It checks:

- M7 still passes;
- the optional M4 backend compiles from normal package files;
- the example installs M4 through `transvoxel_m4_backend.h`;
- existing `tv_build_transition_cell()` calls route through M4 only after
  explicit install;
- uninstall restores the default independent backend;
- `tools/build_dist.py` lists the optional M4 files in the core package
  manifest.

M8 does not rebuild `dist/transvoxel_0bsd_core.zip` and does not prove official
`Transvoxel.cpp` topology equivalence.

Run:

```text
RUN_M8.cmd
```
