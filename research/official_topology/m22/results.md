# M22 Exact Compatibility Claim Boundary

M22 keeps the M21 functional replacement evidence green and locks the stronger exact official-compatibility claims behind explicit blockers.

- Status: `PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY`
- Transvoxel export validation: `validates Transvoxel table ABI against canonical JSON; default transition source is clean-room M4 published-topology behavior; not official Transvoxel.cpp byte clone`
- Consumer compatibility: `PASS_M21_TRANSVOXEL_CPP_CONSUMER_COMPATIBILITY`
- Claim-boundary validation: `PASS_M22_EXACT_COMPATIBILITY_CLAIM_BOUNDARY`
- Readiness: `READY_FUNCTIONAL_FULL_TRANSVOXEL_CPP_REPLACEMENT_EXACT_COMPATIBILITY_BLOCKED`
- Next milestone: `M23_FUNCTIONAL_RELEASE_HARDENING_NO_LOCAL_ZIP`

## Allowed now

Functional clean-room Transvoxel.cpp replacement through the public C/C++ API: default regular and transition builders use clean-room published behavior; C and C++ consumers can compile/link; callback customization is retained.

## Still not allowed

- Exact official Transvoxel.cpp table layout claim.
- Official 73-class ID compatibility claim.
- Official vertex/reuse encoding compatibility claim.
- Exact official transition triangulation identity claim.
- Exact official regular table identity claim.
- Byte-for-byte Transvoxel.cpp table/file identity claim.

No zip/package artifact is built by this milestone runner.
