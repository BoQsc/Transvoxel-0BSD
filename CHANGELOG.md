# Changelog

## Unreleased

- Added a project-wide 0BSD-versus-MIT production choice guide and aligned
  current embedding, release, proof, provenance, and testing documentation.
- Documented that the independent path matches counts, crossing-edge sets, and
  tested seam boundaries for every case while using different valid interior
  connectivity in 170/256 regular and 373/512 transition cases.
- Made the production recommendation explicit: prefer the MIT exact path for
  conservative compatibility; choose 0BSD deliberately when its provenance
  benefit justifies target-engine qualification.
- Added no-archive package refresh and validation modes:
  `build_dist.py --no-zip` and `release_candidate_report.py --package-dir`.
- Synchronized the tracked unpacked core package without rebuilding the ZIP.
- Added an enforced file-level license boundary: the independent public core,
  generator/validation code, and aggregate reports remain 0BSD; six exact
  selection-bearing M24-M26 artifacts are explicitly MIT.
- Removed per-case triangulation details from committed M23/M24 comparison
  reports and retained aggregate counts, hashes, categories, and decisions.
- Added `tools/validate_license_boundary.py` to prevent MIT exact artifacts
  from entering public 0BSD trees or the distribution file list.
- Added M27 as the terminal exact-0BSD roadmap decision; no M28 is selected.
- Re-ran the independent 768-case oracle comparison: exact oriented topology
  matches 86/256 regular and 139/512 transition cases.
- Audited the official dissertation and recorded that published boundary rules
  permit multiple legal interior triangulations rather than uniquely deriving
  every authored official choice.
- Recorded the final split: functional non-exact 0BSD replacement is ready,
  exact semantic integration is technically proven, and the exact 0BSD
  replacement goal is not achieved under the current provenance policy.
- Added M26 pinned Godot Voxel table-source integration using Zig C++.
- Matched all 256 regular cases, 512 transition cases, and 13 transition-corner
  records between the downstream table file and the exact candidate.
- Compiled and linked the complete pinned Godot Voxel Windows GDExtension with
  the replacement table using Zig.
- Split exact semantic drop-in readiness from numeric class-ID and byte
  identity claims; provenance is now the only exact-candidate 0BSD release
  blocker.
- Added M18 exhaustive published transition reference-convention proof.
- Added C helpers converting between the stable M4 row-major case index and
  the dissertation Figure 4.17 case index.
- Proved all 512 index mappings, all 4096 D4 mapping combinations, outward and
  inverse winding, and all six right-handed face frames without official table
  arrays.
- Added M19 proof of published transition topology behavior: all public
  face-contour rules, D4/inversion behavior classes, closed boundaries, and
  minimal genus-zero fillings for all 512 cases.
- Replaced the default fixed-diagonal regular table with an M20 clean-room
  preferred-polarity modified-Marching-Cubes derivation and exhaustive
  regular/regular plus regular/M4 seam proof.

## v34

- Fixed GitHub-ready repository check so local generated proof/cache files created during CI do not fail unless they are tracked by Git.
- Added `docs/RELEASE_NOTES_V34.md`.


## v33

GitHub-ready repository cleanup.

- Added GitHub Actions workflow for the generator/proof suite and C smoke test.
- Added issue templates for bugs, correctness/topology concerns, and feature requests.
- Added pull request template with provenance and proof checklist.
- Added GitHub release page text and publishing checklist.
- Added repository layout documentation.
- Added GitHub-ready validation report.

No geometry, table, or C API behavior changed in v33.

## v32

Release-candidate cleanup for the independent 0BSD core.

- Clean public README and small core package.
- Public release docs, known limits, and release-candidate checklist.
- `dist/transvoxel_0bsd_core.zip` checked by `release_candidate_report.py`.

## Earlier versions

Earlier versions built the clean-room generator, proof suite, Godot validators, scripted auto-interaction, C core, dist package, strict proof matrix, and separate official-topology research track.
