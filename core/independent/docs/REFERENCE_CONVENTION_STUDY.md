# Reference Convention Study

This document records what still has to be proven before claiming official-reference convention equivalence.

## We currently prove

- Our generated transition tables are internally consistent.
- Our side-face fingerprints match across neighboring transition cells.
- Godot seam metrics report zero seam open edges under scripted fields and edits.
- The C core compiles and runs with the generated tables.

## We do not yet prove

- That our 9 sample index order matches the official sample numbering.
- That our high-face / low-face orientation matches the official tables.
- That our inside/outside sign polarity matches Eric's table polarity.
- That our winding convention matches the reference after inversion and rotation.
- That our generated triangles are topologically identical to the official 73-class triangulations.

## Convention proof plan

A future proof should define a small explicit convention object:

```json
{
  "sample_order": "documented 3x3 high face plus low side samples",
  "inside_sign": "value < isolevel",
  "face_axes": "documented right-handed local frame",
  "transition_direction": "low-resolution cell face looking toward high-resolution neighbor",
  "winding": "front faces point toward decreasing density or documented normal side"
}
```

Then every generated case should be tested under all six face directions by transform matrices, not by hand inspection.

## Current v29 status

`validate_reference_convention.py` checks internal convention consistency. It does not prove official-reference equivalence.

