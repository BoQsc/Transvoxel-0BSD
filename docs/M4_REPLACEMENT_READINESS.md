# M4 Replacement Readiness

The project has four different readiness questions. They must not be collapsed
into one claim.

## 1. Optional transition-backend candidate

This requires the M4 table/runtime, C API, package, terrain export, Godot mesh,
backend comparison, and scripted edit milestones to pass.

Current status: machine-checked by
`validation/m4_replacement_readiness_report.json`.

## 2. Default transition-backend replacement

In addition to the candidate milestones, this requires:

```text
M4 validation in all six transition-face orientations
M4-specific multi-face/corner junction validation
the full production gate with M4 installed through the normal backend API
```

The first item is proven by M15, the second by M16, and the production gate by
M17. The readiness report now permits replacing the default transition backend.

## 3. Functional full Transvoxel.cpp replacement

In addition to default-backend readiness, this requires:

```text
independently proven official transition topology behavior
independently proven published sign/orientation/reference convention
clean-room regular-cell equivalence
a documented and tested consumer compatibility contract
```

The reference-convention item is proven by M18. Transition topology,
regular-cell equivalence, and consumer compatibility remain blocking.

Byte-for-byte identity is not required for functional replacement.

## 4. Exact table/encoding compatibility

This additionally requires:

```text
official 73-class ID mapping
official vertex/reuse encoding equivalence
exact table identity if that exact claim is made
```

Official table arrays must never be used as generator inputs or tuning oracles.

Run:

```text
RUN_M14.cmd
RUN_M15.cmd
RUN_M16.cmd
RUN_M17.cmd
RUN_M18.cmd
```

The current expected result is a passing readiness analysis with the
default-transition-backend decision ready, the functional full replacement
decision blocked, and M19 transition-topology validation selected as the next
milestone.
