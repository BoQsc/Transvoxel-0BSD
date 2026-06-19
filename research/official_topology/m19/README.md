# M19: published transition-topology behavior

M19 proves the clean-room M3/M4 transition candidate satisfies the published
topology behavior needed by a functional implementation:

- the preferred-polarity full- and half-face contour rules;
- all lateral-face configurations from dissertation Figure 4.10;
- the published D4 and conditional-inversion class construction;
- `51 + 18 + 4 = 73` clean-room behavior classes covering all 512 cases;
- closed degree-2 boundary loops;
- minimal boundary-only genus-zero surfaces preserving every contour;
- M4 class transforms, topology, and winding preservation.

This is behavioral equivalence. It does not claim identical official interior
diagonals, numeric class IDs, vertex/cache codes, or table bytes.

Run:

```text
RUN_M19.cmd
```
