# Production Proof Data Dump

Status: **DATA_DUMP_ONLY_NOT_PRODUCTION_PASS**

This file is intentionally not a visual validation report. It records the table and proof data that must be inspected before trusting any rendered screenshot.

## Table summary

- Regular cases: 256
- Regular triangles: 1920
- Transition cases: 512
- Transition triangles: 12288
- Transition boundary triangles: 22
- Transvoxel export schema: `boqsc.transvoxel_tables.v1`

## Required next data before production proof

- godot/runtime_dump.json from res://scripts/DumpRuntimeData.gd
- godot/mesh_api_dump.json from res://scripts/DumpMeshData.gd
- real LOD0-transition-LOD1 seam_metrics.json with seam_open_edges only, not total outer edges
- all six chunk-face directions with multiple SDF fields and live edit regeneration

## Generated files

- `proof/proof_dump.json`
- `proof/tables/regular_case_metrics.csv`
- `proof/tables/transition_case_metrics.csv`
- `proof/tables/transition_face_segments.csv`
