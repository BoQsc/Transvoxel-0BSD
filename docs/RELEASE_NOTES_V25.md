# Release Notes v25

v25 adds a strict correctness audit layer.

New tools:

```text
tools/validate_73_classes.py
tools/validate_winding_normals.py
tools/validate_self_intersections.py
tools/validate_reference_convention.py
tools/validate_corner_junctions.py
tools/strict_correctness_audit.py
```

New docs:

```text
docs/PROOF_MATRIX.md
```

New reports:

```text
validation/strict_correctness_audit.json
validation/equivalence_class_report.json
validation/winding_normals_report.json
validation/self_intersection_report.json
validation/reference_convention_report.json
validation/corner_junction_report.json
```

Important outcome:

```text
Transvoxel-style proof: PASS
Official Transvoxel equivalence proof: NOT_PROVEN
```

The package now makes the missing official-equivalence claims explicit instead of implying them.
