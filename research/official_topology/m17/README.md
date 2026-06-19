# M17: M4-selected production gate

M17 combines the previously separate M4 evidence into one production-readiness
decision.

It requires:

- M4 installation through the normal `transvoxel.h` backend hook;
- all 512 cases through `tv_build_transition_cell()`;
- mapped edge/corner cells in the same C process;
- M4 terrain export through the normal API;
- actual Godot scripted-edit execution;
- six-face orientation and mapped corner-junction milestones;
- the existing base production gate.

Run:

```text
RUN_M17.cmd
```

A passing M17 allows the readiness report to say M4 is ready to replace the
default transition backend. It still does not allow a full `Transvoxel.cpp`
replacement claim because official transition/reference behavior, regular-cell
equivalence, and consumer compatibility remain unproven.
