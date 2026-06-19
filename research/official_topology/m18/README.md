# M18: published reference-convention validation

M18 proves the clean-room M4 transition candidate uses the same published
algorithmic convention described by the dissertation, with one explicit
non-identity case-index permutation.

The runtime table remains indexed by local row-major sample bits. Public C
helpers convert between that stable index and Figure 4.17's bit weights.

M18 exhaustively validates:

- the Figure 4.16 sample coordinates and half-face corner correspondence;
- negative scalar values as inside/solid;
- all 512 local/reference index mappings and inverse mappings;
- complement and 180-degree rotation properties;
- all 4096 D4 transform/index combinations;
- coherent outward winding toward increasing scalar values;
- reversed winding for all same-topology complement pairs;
- all six orientation-preserving M4 face frames;
- the conversion API and all 512 runtime builds with Zig C99.

This does not prove official triangulation topology, class IDs, vertex/cache
encoding, or table bytes.

Run:

```text
RUN_M18.cmd
```
