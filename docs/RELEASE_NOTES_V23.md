# v23 release-candidate cleanup

v23 focuses on public usability instead of adding more proof layers.

Changes:

```text
README.md rewritten for public users
README_CORE.txt rewritten for the small dist package
docs/DROP_IN.md expanded
docs/API.md expanded
docs/WHAT_THIS_PROVES.md added
docs/RELEASE_NOTES_V23.md added
examples/c_terrain_export/ added
build_dist.py now includes the public proof/claim docs and C terrain example
VERSION updated to v23
```

Intentionally not added:

```text
C++ example
D example
new Godot proof stage
new table format
```

Reason:

```text
The project already has a strong automated proof baseline. v23 makes the core
package easier to understand and embed.
```
