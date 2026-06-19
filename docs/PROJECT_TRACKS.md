# Project Tracks

v31 splits the project into two explicit tracks.

## Track 1: Independent 0BSD Core

Location:

```text
core/independent/
```

Purpose:

```text
A practical, engine-independent, 0BSD voxel LOD transition core.
```

Status:

```text
independent_core: PASS candidate
official_transvoxel_equivalence: NOT_CLAIMED
```

This track is allowed to be used as a product candidate because it has its own proof gate: generator proof, C compile proof, Godot seam proof, scripted edit proof, and external alignment reports.

It must not be silently mutated by official-equivalence experiments.

## Track 2: Official Topology Research

Location:

```text
research/official_topology/
```

Purpose:

```text
Research whether a no-copy 0BSD implementation can derive the official-style 73-class Transvoxel topology and reference convention.
```

Status:

```text
official_73_class_mapping: NOT_PROVEN
published_reference_sign_orientation_equivalence: PROVEN_M18
published_transition_topology_behavior: PROVEN_M19
clean_room_regular_cell_equivalence: PROVEN_M20
exact_official_triangulation_identity: NOT_PROVEN
```

This track may fail, change direction, or produce new candidate generators. It should not break the independent core.

## Why this split exists

v30 showed that the current independent tetrahedralized transition topology does not naturally collapse to the official 73-class target. That means official-equivalence research should be treated as a separate topology research problem, not as a small patch to the working core.

## Release wording

Acceptable wording:

```text
Independent 0BSD Transvoxel-style voxel LOD transition core.
```

Not acceptable wording:

```text
Public-domain clone of Eric Lengyel's Transvoxel.cpp.
```
