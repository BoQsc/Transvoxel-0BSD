# Boundary Contours

M3 derives a contour graph on the six transition-cell faces before attempting any interior triangulation.

## Full-resolution face

The 3 by 3 sample grid is divided into four quadrants:

```text
6 -- 7 -- 8
|    |    |
3 -- 4 -- 5
|    |    |
0 -- 1 -- 2
```

Each quadrant uses the preferred-polarity marching-squares rule:

- zero sign-changing edges produce no segment;
- two sign-changing edges are connected;
- in the four-edge ambiguous pattern, crossings on edges sharing an inside corner are connected.

Complementing an ambiguous quadrant therefore selects the other legal connectivity. This is why ambiguity-bearing inverse cases cannot always share one class.

## Half-resolution face

The four half-resolution samples inherit signs from full-resolution corners:

```text
9  <- 0
10 <- 2
11 <- 6
12 <- 8
```

The half-resolution square uses the same preferred-polarity rule.

## Lateral faces

Each lateral face is controlled by three full-resolution samples `a, b, c`; its two half-resolution endpoints repeat the signs of `a` and `c`.

- If `a` and `c` differ, one full-face crossing connects to one half-face crossing.
- If the signs alternate, `a == c != b`, the two full-face crossings connect directly and the contour does not reach the half-resolution face.
- Uniform signs produce no contour.

These rules produce a degree-2 boundary graph for every one of the 512 cases.
