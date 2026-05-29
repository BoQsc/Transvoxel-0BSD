# Repository Layout

```text
include/                    public C header
src/                        public C implementation
generated/                  generated public table header
examples/                   C examples
dist/                       generated small public core zip
tools/                      generators, validators, release tools
godot/                      validator/sandbox only; not required by the core
validation/                 generated proof reports
proof/                      one-click reporting bundle and proof dump outputs
core/independent/           frozen copy of the proven independent core track
research/official_topology/ no-copy official-topology research track
docs/                       API, proof, release, and research docs
.github/                    CI, issue templates, PR template
```

The product artifact is `dist/transvoxel_0bsd_core.zip`.

The full repository is for maintainers and auditors.
