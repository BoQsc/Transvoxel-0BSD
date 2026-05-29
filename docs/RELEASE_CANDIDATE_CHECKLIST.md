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
