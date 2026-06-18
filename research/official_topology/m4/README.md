# M4 Runtime Candidate Tables

M4 turns the M3 clean-room official-topology research output into runtime-ready candidate tables.

It does not copy or compare against Eric Lengyel's MIT `Transvoxel.cpp` lookup arrays. It also does not claim official equivalence.

Run:

```text
RUN_M4.cmd
```

or:

```text
python research/official_topology/m4/run_m4.py
```

Outputs:

```text
generated/official_topology_candidate_tables.json
generated/official_topology_candidate_tables.h
research/official_topology/m4/runtime_table_validation.json
research/official_topology/m4/zig_header_smoke.json
research/official_topology/m4/m4_report.json
research/official_topology/m4/results.md
```

The generated table contains:

- 512 transition cases;
- 73 M3 research classes;
- D4/complement transform metadata from each class representative to each case;
- per-case runtime vertex-pair and triangle records;
- flat C-friendly arrays;
- explicit `NOT_PROVEN` official-equivalence fields.

When Zig is available, M4 also compiles and runs a tiny C99 include smoke test
for `generated/official_topology_candidate_tables.h`. Zig is discovered through
the same repo-local setup used by `tools/test_core_c.py`: `zig_path.txt`,
`c_compiler_path.txt`, `ZIG_EXE`, PATH, or the narrow project-local auto-search.

M4 is a candidate replacement path. It is intentionally separate from the current default C core until stricter equivalence and production-integration work is complete.
