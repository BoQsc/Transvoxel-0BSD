# M3 Report Schemas

All M3 outputs are JSON with explicit schema and status fields.

## `class_partition.json`

Contains:

- 73 research class records;
- all member cases;
- representative cases;
- inverse split relationships;
- a 512-entry case-to-research-class map;
- overlap and coverage checks.

## `boundary_loops.json`

Contains, for every case:

- per-face contour segments;
- closed boundary loops;
- loop lengths;
- ambiguity flags;
- research class ID.

## `candidate_triangulations.json`

Contains, for every case:

- boundary loops;
- candidate triangles expressed as sample-edge intersection keys;
- triangulation method;
- manifold and intersection validation;
- class-representative summaries.

## `independent_core_comparison.json`

Compares only against this repository's independent generated table:

- exact boundary segment geometry;
- connectivity after contracting extra independent-core boundary vertices;
- ambiguity classification of mismatches;
- triangle-count differences.

No output contains or compares official table arrays.

## `m3_report.json`

Small aggregate report intended for automation and milestone review.
