# Proof Suite Report

Overall: **PASS**

This proof suite validates the generated 0BSD tables against their own documented table contract. It does not claim byte-for-byte identity with any external table file.

## Steps

- `PASS` — `tools/generate_regular.py --out generated` — 0.053s
- `PASS` — `tools/generate_transition.py --out generated` — 0.285s
- `PASS` — `tools/export_transvoxel.py` — 0.146s
- `PASS` — `tools/sync_godot_tables.py` — 0.038s
- `PASS` — `tools/verify_generated_tables.py` — 0.145s
- `PASS` — `tools/validate_tables.py` — 0.116s
- `PASS` — `tools/validate_transition.py` — 0.145s
- `PASS` — `tools/validate_transvoxel.py` — 0.458s
- `PASS` — `tools/validate_boundaries.py` — 0.134s
- `PASS` — `tools/validate_neighbors.py` — 0.138s
- `PASS` — `tools/validate_chunks.py` — 1.092s
- `PASS` — `tools/validate_godot_project.py` — 0.08s
- `PASS` — `tools/dump_proof_data.py` — 0.168s
- `PASS` — `tools/external_alignment_report.py` — 0.021s
- `PASS` — `tools/topology_signature_analysis.py` — 0.96s
- `PASS` — `tools/official_equivalence_research.py` — 0.065s
- `PASS` — `tools/topology_comparison_no_copy.py` — 0.019s
- `PASS` — `research/official_topology/derive_transition_classes.py` — 0.002s
- `PASS` — `research/official_topology/derive_reference_convention.py` — 0.002s
- `PASS` — `research/official_topology/derive_candidate_73_classes.py` — 0.339s
- `PASS` — `research/official_topology/reference_convention_matrix.py` — 0.003s
- `PASS` — `research/official_topology/official_topology_constraints.py` — 0.042s
- `PASS` — `tools/strict_correctness_audit.py` — 3.275s
- `PASS` — `tools/project_tracks_report.py` — 0.006s
- `PASS` — `tools/build_dist.py` — 0.183s
- `PASS` — `tools/release_candidate_report.py` — 0.003s
- `PASS` — `tools/github_ready_report.py` — 0.003s

## What this proves

- The regular and transition tables regenerate deterministically.
- The exported transvoxel_tables ABI round-trips to the canonical JSON.
- The generated C header is readable by a C compiler when one is available.
- All 512 transition cases expose the expected boundary contour from the documented transition-cell boundary triangulation.
- Side-face contour fingerprints are deterministic and match on opposite side faces.
- Deterministic chunk strips from several sign fields have matching shared side-face fingerprints.
- The Godot validation project is packaged with the expected scene, scripts, and generated JSON tables copied from the canonical generated outputs.
- A non-visual proof data dump is written to proof/proof_dump.json and proof/tables/*.csv before visual validation is trusted.
- Failure OBJ export is available as a separate diagnostic command: python tools/export_failure_obj.py.
- An external-alignment report checks the generated project against published Transvoxel-style outcome requirements.
- A topology-signature analysis groups all 512 generated transition cases by generated topology without reading external table values.
- An official-equivalence research report documents the no-copy boundary, 73-class status, naive symmetry orbit counts, and topology-signature status.
- A topology-comparison report compares public structural expectations without reading external table values.
- A strict correctness audit checks duplicates, degenerates, complement winding, midpoint self-intersections, 73-class status, reference convention status, and corner-junction evidence.
- A project-tracks report freezes the working independent core separately from the official-topology research track.
- Track B research now runs a no-copy candidate 73-class derivation search, an internal reference convention matrix, and public structural constraint checks.
- A release-candidate report verifies the small public core zip contains expected files and no proof/Godot/research clutter.
- A GitHub-ready report verifies release text, issue templates, CI workflow, and repository publishing files are present.

## What this does not prove

- It does not prove byte-for-byte compatibility with Eric Lengyel's MIT-licensed Transvoxel.cpp tables.
- It does not prove the table has the official 73-equivalence-class compression.
- It does not prove the Godot scene was executed unless you also run Godot locally.
- It does not replace the final production terrain/chunk/GDExtension integration.
- It does not pass the production gate until Godot runtime dumps and real seam_metrics.json exist.
- It does not prove exact visual/artistic terrain quality in a finished game world.
- It still marks official 73-class equivalence, exact reference sign/orientation convention equivalence, and original topology equivalence as NOT_PROVEN.
- It does not claim exhaustive proof for every possible production corner or multi-neighbor streaming junction.
- It keeps official-topology research separate and explicitly IN_PROGRESS / NOT_PROVEN.
- It does not treat the 70-class C4+complement observation or any candidate orbit split as official 73-class proof.
