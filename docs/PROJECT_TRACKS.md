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
exact_official_triangulation_identity: PROVEN_M24
official_oracle_baseline: COMPLETE_M23
exact_regular_transition_topology: PROVEN_M24
exact_candidate_0bsd_provenance: NOT_CLEARED
compatible_transvoxel_cpp_data_abi: PROVEN_M25
unchanged_style_cpp_consumer: PROVEN_M25
godot_voxel_table_integration: PROVEN_M26
godot_voxel_full_gdextension_build: PASS_M26_ZIG
exact_semantic_drop_in_integration: READY_M26
exact_semantic_drop_in_0bsd_release: TERMINAL_NOT_ACHIEVED_M27
exact_replacement_finish_line: CLOSED_NOT_ACHIEVED
next_milestone: NONE_TERMINAL
```

This track may fail, change direction, or produce new candidate generators. It should not break the independent core.

M23 uses a verified external MIT checkout only as an isolated comparison
oracle. The repository stores case-level booleans, counts, and hashes, not
oracle arrays. M24 targets the measured topology mismatches before any
unchanged-consumer integration claim.

M24 now resolves those topology mismatches in the isolated research candidate:
256/256 regular and 512/512 transition oriented topologies match. M25 owns
vertex ordering/reuse encoding, class/table layout, and unchanged-consumer
compatibility.

M25 now proves compatible original data symbols and capacities, packed reuse
semantics, and unchanged-style C++ consumption. It uses independent internal
class IDs.

M26 proves the pinned Godot Voxel table-source replacement contract across all
781 records and compiles/links the full Windows GDExtension with Zig. M27 is
terminal: the independent deterministic rule matches exact oriented topology
in only 86/256 regular and 139/512 transition cases, while the publication
permits multiple legal interiors. The exact candidate reaches 256/256 and
512/512 by using MIT-oracle-calibrated selections, so the exact 0BSD goal is not
achieved under the current provenance policy. There is no automatic M28.

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
