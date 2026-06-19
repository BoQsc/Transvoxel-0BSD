# License Scope

This repository has a strict file-level license boundary.

## 0BSD scope

The root [`LICENSE`](LICENSE) applies to the independently derived public core,
generator and validation source code, documentation, and aggregate comparison
reports unless a file explicitly declares another license.

The public core under `include/`, `src/`, `generated/`, and
`core/independent/` is 0BSD. It does not contain the exact oracle-calibrated
data listed below.

## MIT exact-compatibility data

The exact selection-bearing generated artifacts listed in
`research/official_topology/MIT_ARTIFACTS.json` are licensed MIT, not 0BSD.
Their license is [`LICENSES/MIT.txt`](LICENSES/MIT.txt), copyright Eric Lengyel
2009. Each C/C++ artifact carries an MIT SPDX header, and each JSON artifact
carries equivalent machine-readable license metadata.

These MIT artifacts are isolated research/integration data. They are excluded
from the public 0BSD core and its distribution file list.

## Aggregate reports

The M23-M27 comparison and audit reports remain 0BSD. They may contain counts,
statuses, hashes, mismatch categories, and provenance decisions. They must not
contain official arrays, exact candidate arrays, per-case triangulations, or
oracle-selected option indexes.

Run `python tools/validate_license_boundary.py` to enforce this separation.
