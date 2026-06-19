# Exact Compatibility Claim Boundary

M22 locks the public claim boundary after M21.

Allowed public claim:

```text
Functional clean-room Transvoxel.cpp replacement through the public C/C++ API.
```

That means:

```text
default regular cells use the M20 clean-room preferred-polarity table
default transition cells use the M21 clean-room M4 published-topology table
C consumers can compile and run the public API
C++ consumers can include transvoxel.h and link against a C object
callback customization is retained
```

Not allowed without future exact evidence:

```text
Exact official Transvoxel.cpp table layout claim.
Official 73-class ID compatibility claim.
Official vertex/reuse encoding compatibility claim.
Exact official transition triangulation identity claim.
Exact official regular table identity claim.
Byte-for-byte Transvoxel.cpp table/file identity claim.
```

Byte identity is not required for functional replacement. Byte identity is
required before claiming exact official table-file compatibility.

The boundary is machine-checked by:

```text
python tools/validate_exact_compatibility_claim_boundary.py
```

The expected report status is:

```text
PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY
```

Official arrays remain forbidden as generator inputs, tuning oracles, or copied
data sources. Exact compatibility work, if ever pursued, must remain a separate
no-copy research track.
