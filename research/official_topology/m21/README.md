# M21 - Default M4 Functional Consumer Compatibility

M21 switches the public default transition export to the clean-room M4 published-topology table and proves the functional C/C++ consumer contract.

It does not build a zip artifact and it does not claim exact official `Transvoxel.cpp` table layout, class IDs, vertex encoding, triangulation identity, or byte identity.

Run:

```text
python research/official_topology/m21/run_m21.py
```

Expected pass status:

```text
PASS_M21_DEFAULT_M4_FUNCTIONAL_CONSUMER_COMPATIBILITY
```
