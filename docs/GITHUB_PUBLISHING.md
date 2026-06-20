# GitHub Publishing Checklist

## Repository setup

Suggested repository description:

```text
Independent 0BSD Transvoxel-style voxel LOD transition core with generated tables and proof tools.
```

Suggested topics:

```text
voxel transvoxel lod terrain marching-cubes marching-tetrahedra c 0bsd public-domain-style godot validation
```

## Before pushing

Run at least:

```sh
python tools/prove_tables.py
python tools/test_core_c.py
python tools/build_dist.py
python tools/release_candidate_report.py
python tools/github_ready_report.py
```

When this environment should validate the unpacked package without creating or
replacing a ZIP, use:

```sh
python tools/build_dist.py --no-zip
python tools/release_candidate_report.py --package-dir
```

On Windows with Godot installed, run:

```text
RUN_FULL.cmd
```

Upload or archive:

```text
proof/SEND_TO_CHATGPT.zip
```

## Release assets

Use:

```text
dist/transvoxel_0bsd_core.zip
```

as the small public drop-in package.

Use the full source zip for people who want the generator/proof/Godot validation stack.

Release notes must link `docs/CHOOSING_0BSD_OR_MIT.md` and state that production
should begin with the official upstream MIT `Transvoxel.cpp` behind a stable
adapter. The 0BSD package remains an optional backend until it passes
equivalent long-term visual, collision, LOD, editing, streaming, and
performance qualification.

## Claims to keep

Safe claim:

```text
Independent 0BSD Transvoxel-style voxel LOD transition core.
```

Do not claim:

```text
Official Transvoxel.cpp under public domain.
Official 73-class equivalence proven.
Byte-identical or table-identical to Eric Lengyel's MIT tables.
Equal production history or equal per-case interior topology to the MIT exact path.
```

## Tagging

Recommended tag format:

```text
v33
```

Do not tag a release as official-equivalent unless the official-topology research track produces a separate proof.
