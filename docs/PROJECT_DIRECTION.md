# Project direction

The main product is an engine-independent 0BSD/public-domain-style voxel LOD transition core.

Godot is only a validator and future interactive evaluation sandbox. The core must remain usable outside Godot.

Current release shape:

```text
Full proof/dev package:
  generators, validation tools, Godot validator, reports, C core, docs

Small drop-in package:
  dist/transvoxel_0bsd_core.zip
```

Final personal proof remains interactive terrain evaluation: walking, digging, placing/removing terrain, and verifying the seam metrics stay clean.
