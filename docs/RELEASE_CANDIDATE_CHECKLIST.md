# Release Candidate Checklist

A release-candidate run is acceptable when all of these are true:

```text
RUN_FULL.cmd status: PASS
production_gate: PASS
external_alignment_report: PASS
strict_correctness_audit.transvoxel_style_proof: PASS
strict_correctness_audit.official_transvoxel_equivalence_proof: NOT_PROVEN
core C test: PASS when a C compiler is available
dist/transvoxel_0bsd_core.zip: built
release_candidate_report: PASS
```

The `NOT_PROVEN` official-equivalence result is intentional. It prevents the project from making stronger claims than the proof supports.

For the current repository-wide result, also confirm:

```text
MIT exact semantic topology/integration: PROVEN_M24_TO_M26
exact semantic 0BSD release: NOT_ACHIEVED_M27
production selection guide: docs/CHOOSING_0BSD_OR_MIT.md
```

The release must not imply equal production history or equal per-case interior
topology. The main recommendation is to start with the official upstream MIT
`Transvoxel.cpp`, build a battle-tested baseline behind an adapter, and move to
0BSD only after equivalent target-engine qualification.

The small core zip should not contain:

```text
proof/
runs/
validation/*.json
godot/
research/
*.cache
SEND_TO_CHATGPT.zip
```

The full repository zip may contain proof tools and research files.
