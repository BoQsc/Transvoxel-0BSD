# Release Notes v31

v31 creates a two-track project structure.

Added:

```text
core/independent/
research/official_topology/
tools/project_tracks_report.py
docs/PROJECT_TRACKS.md
docs/RELEASE_NOTES_V31.md
```

The independent core is frozen as a practical 0BSD core candidate. Official-equivalence research now happens in a separate folder so it cannot destabilize the proven core.

The proof suite now reports:

```text
independent_core: PASS
official_topology_research: IN_PROGRESS
official_equivalence: NOT_PROVEN
```

No geometry behavior changed in v31.
