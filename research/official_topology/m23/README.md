# M23 - Official Oracle Baseline

M23 switches the active roadmap from functional release hardening to exact
replacement work.

It compares all 256 regular and 512 transition cases with a verified external
checkout of Eric Lengyel's MIT `Transvoxel.cpp`. The MIT source stays outside
this repository. Reports contain only hashes, counts, and mismatch categories;
they do not reproduce oracle arrays.

Run:

```text
python research/official_topology/m23/run_m23.py
```

Expected baseline status:

```text
PASS_M23_OFFICIAL_ORACLE_BASELINE_EXACT_REPLACEMENT_NOT_READY
```

That status means the exhaustive baseline completed successfully. Exact
replacement remains blocked until every topology, encoding, layout, and
unchanged-consumer integration gate passes.
