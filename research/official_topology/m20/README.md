# M20: clean-room regular-cell equivalence

M20 replaces the old fixed-diagonal marching-tetrahedra regular table with an
independently derived modified-Marching-Cubes table using the same published
preferred-polarity rule as M4.

It proves:

- Figure 3.8 corner numbering and Listing 3.1 case bits;
- 256 cases and 18 rotation/inversion behavior classes;
- vertices only on active cube edges;
- at most 12 vertices and 5 triangles per cell;
- 820 triangles across all 256 cases;
- coherent outward winding and nonintersecting triangle complexes;
- 12,288 exhaustive regular/regular shared-face comparisons;
- 40,960 exhaustive regular/M4 full- and half-face comparisons;
- all 256 cases through the public C API with Zig;
- actual Godot loading of the regenerated regular table.

Exact official class numbers, reuse codes, and table bytes remain separate.

Run:

```text
RUN_M20.cmd
```
