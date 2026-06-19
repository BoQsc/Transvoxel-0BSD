# M17 M4-Selected Production Gate

M17 combines the normal C backend hook, mapped corner geometry, terrain export, Godot scripted edits, six-face validation, corner junctions, and the base production gate.

- Status: `PASS_M17_M4_SELECTED_PRODUCTION_GATE_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M16 status: `PASS_M16_M4_DEFORMED_CORNER_JUNCTIONS_OFFICIAL_EQUIVALENCE_NOT_PROVEN`
- M4 production gate: `PASS_M4_SELECTED_PRODUCTION_GATE`
- Godot scripted-edit runtime executed: `True`

## Combined C assembler

- Normal API cases: `512`
- Normal API vertices/triangles: `4096` / `2640`
- Mapped builds: `672`
- Mapped vertices/triangles: `2372` / `1464`
- Default backend restored: `1`
- Failures: `0`

## Readiness effect

- M4-selected production gate: `PASS`
- Ready to replace default transition backend: `True`
- Functional full replacement ready: `False`
- Remaining blocking gates: `7`
- Next milestone: `M18_OFFICIAL_REFERENCE_CONVENTION_VALIDATION`

M17 proves the M4 candidate's default-backend production gate. It does not prove official reference/topology behavior or a full Transvoxel.cpp replacement.
