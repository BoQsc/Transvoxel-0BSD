# Independent Core Track

This folder is the frozen **M21 working 0BSD core** track.

It exists so the proven drop-in C core can remain stable while official-topology research happens elsewhere.

Status:

```text
independent_core: PASS functional replacement snapshot
license: 0BSD
product target: small engine-independent C core
functional_transvoxel_cpp_replacement: PROVEN through public C/C++ API
official_transvoxel_equivalence: NOT_PROVEN
```

Use this track when you want the practical library:

```text
include/transvoxel.h
src/transvoxel.c
generated/transvoxel_tables.h
```

The official-topology research track is separate by design and must not mutate this core unless a new proof gate passes.

M21 sync note: the default regular table is the clean-room M20 table and the
default transition table is the clean-room M4 published-topology table. Exact
official class IDs, vertex encoding, triangulation identity, and byte identity
remain outside this snapshot's claim.

M22 sync note: the exact compatibility claim boundary is documented and
machine-checked. This snapshot may be described as a functional clean-room
replacement through the public C/C++ API, not as an exact official table clone.
