# Stage 12: M4 corner junctions

This headless Godot stage validates mapped, non-box M4 transition cells where
three perpendicular LOD faces meet.

For all eight signed corner octants and deterministic scalar fields it checks:

- shared full- and half-resolution lateral-face sample positions;
- shared sample values;
- coincident lateral boundary geometry;
- opposite boundary-edge winding;
- coherent internal triangle winding;
- common inner-corner positions and values;
- combined `ArrayMesh` and `MeshDataTool` readback.

The deformation follows the public transition-cell geometry: full-resolution
face vertices stay fixed while half-resolution corners are inset to make room
for adjacent transition cells.

The runtime output is:

```text
godot/validation/12_m4_corner_junctions/m4_corner_junctions.json
```

This is clean-room internal junction evidence. It does not prove official table
identity, official class IDs, or official topology equivalence.
