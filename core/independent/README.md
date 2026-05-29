# Independent Core Track

This folder is the frozen **working 0BSD core** track.

It exists so the proven drop-in C core can remain stable while official-topology research happens elsewhere.

Status:

```text
independent_core: PASS candidate
license: 0BSD
product target: small engine-independent C core
official_transvoxel_equivalence: NOT_PROVEN
```

Use this track when you want the practical library:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
```

The official-topology research track is separate by design and must not mutate this core unless a new proof gate passes.
