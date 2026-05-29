# Release Notes v32

v32 is the first release-candidate cleanup after the two-track split.

Focus:

- make the independent 0BSD C core the public product candidate;
- keep Godot as validator/sandbox, not as the required runtime;
- keep official-topology research separate under `research/official_topology/`;
- make the small `dist/transvoxel_0bsd_core.zip` easier to understand and embed;
- add a release-candidate report that checks the public dist package for expected files and local-artifact leakage.

No geometry or table behavior changed in v32.

Current public claim remains:

```text
Independent 0BSD Transvoxel-style voxel LOD transition core: PASS when RUN_FULL passes.
Official Transvoxel.cpp / 73-class table equivalence: NOT_PROVEN.
```

The release-candidate package is intended for users who want a small C core:

```text
dist/transvoxel_0bsd_core.zip
```

The full repository package remains for proof, generators, Godot validation, scripted auto-interaction, and official-equivalence research.
