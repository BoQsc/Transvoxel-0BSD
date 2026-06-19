# Changelog

## Unreleased

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
