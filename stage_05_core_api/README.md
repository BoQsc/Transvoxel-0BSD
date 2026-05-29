# Stage 05 — Core API

This stage turns the proof package into a usable engine-independent core.

Public files:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
examples/c_minimal/main.c
```

Run:

```sh
python tools/test_core_c.py
python tools/build_dist.py
```

The one-click runner also executes these steps.
