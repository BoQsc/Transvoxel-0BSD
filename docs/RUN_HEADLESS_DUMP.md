# Run the Non-Visual Proof Dump

From the package root:

```sh
python tools/prove_tables.py
python tools/dump_proof_data.py
```

Then run the Godot runtime dumps:

```sh
cd godot
godot --headless --path . --script res://scripts/DumpRuntimeData.gd
godot --headless --path . --script res://scripts/DumpMeshData.gd
cd ..
python tools/validate_godot_dump.py
python tools/check_production_gate.py
```

Expected current result:

```text
production gate: BLOCKED
```

That is correct until the real seam assembler writes:

```text
godot/validation/seam_metrics.json
```
