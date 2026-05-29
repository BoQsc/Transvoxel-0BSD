# Release Notes v30

v30 adds the topology-signature research step for official-equivalence work.

## Added

- `tools/topology_signature_analysis.py`
- `validation/topology_signature_report.json`
- `validation/topology_signature_report.md`
- `docs/TOPOLOGY_SIGNATURE_ANALYSIS.md`

## Result

The new topology-signature analysis groups all 512 generated transition cases by
several no-copy topology signatures. None of the generated signature families
matches the public official Transvoxel target of 73 classes.

Observed v30 class counts:

```text
exact_sample_edge_topology:          256
d4_sample_edge_topology:             201
d4_complement_sample_edge_topology:  201
graph_only_topology_coarse:          484
raw_d4_complement_orbit:              51
official target:                      73
```

## Meaning

This does not weaken the current functional proof. The existing generated-table,
C-core, Godot seam, and auto-interaction proof remains valid for this independent
0BSD Transvoxel-style core.

It does strengthen the honesty matrix: official Transvoxel 73-class/topology
equivalence remains **NOT_PROVEN**.

No MIT table values were read or used.
