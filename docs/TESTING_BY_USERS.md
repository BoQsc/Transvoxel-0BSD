# Testing by Users

This document is for people testing the independent 0BSD core outside the original author's machine.

The goal is to collect useful correctness reports, not vague screenshots.

Read `docs/CHOOSING_0BSD_OR_MIT.md` first. Establish the official upstream MIT
`Transvoxel.cpp` as the production baseline behind a stable adapter. Testing
the 0BSD path should specifically determine whether it can replace that
battle-tested baseline despite its different valid interior connectivity.

## Fast path for normal users

Download the latest release asset:

```text
transvoxel_0bsd_core.zip
```

Extract it, then compile the minimal C example.

With Zig:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
./c_minimal
```

With a normal C compiler:

```sh
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o c_minimal
./c_minimal
```

Expected kind of output:

```text
regular case=23 vertices=6 triangles=4
transition case=11 vertices=6 triangles=4
```

## Test the terrain OBJ example

Build the terrain export example.

With Zig:

```sh
zig cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_terrain_export/main.c -o terrain_export
./terrain_export
```

With a normal C compiler:

```sh
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_terrain_export/main.c -o terrain_export
./terrain_export
```

It should write:

```text
terrain_lod_seam.obj
terrain_lod_seam.mtl
terrain_lod_seam_report.txt
```

Open `terrain_lod_seam.obj` in Blender, MeshLab, Godot, or another OBJ viewer.

M4 callback-adapter terrain export:

```sh
zig cc -std=c99 -Iinclude -Igenerated -DTV_EXAMPLE_USE_M4_BACKEND_CANDIDATE src/transvoxel.c src/transvoxel_m4_candidate.c src/transvoxel_m4_backend.c examples/c_terrain_export/main.c -o terrain_export_m4
./terrain_export_m4
```

The material groups are:

```text
green   high LOD regular cells
orange  transition strip
blue    low LOD regular cells
```

## Full repository proof path

Clone the full repository if you want to audit the generator/proof system:

```sh
git clone https://github.com/BoQsc/Transvoxel-0BSD
cd Transvoxel-0BSD
python tools/prove_tables.py
python tools/test_core_c.py
python tools/build_dist.py
python tools/release_candidate_report.py
python tools/github_ready_report.py
```

On Windows, the full package also includes convenience scripts:

```text
RUN_FAST.cmd        quick proof, no production claim
RUN_CORE.cmd        C core compile + dist package
RUN_FULL.cmd        full local release proof, including Godot steps when available
```

Godot runtime validation requires a local Godot install. The core C package itself does not require Godot.

## What to include in a correctness report

Useful reports should include:

```text
operating system
compiler name and version
release tag or commit SHA
which example or integration was tested
exact command line used
console output
whether OBJ files were created
whether cracks, holes, duplicate triangles, wrong normals, or degenerate triangles were observed
whether rendered normals, lighting, collision, or contact behavior differs from the official upstream baseline
whether repeated edits or LOD switches produce visible or physical popping
representative streaming and performance results
smallest reproducible case if something fails
```

For full repository runs, attach:

```text
validation/*.json
proof/SEND_TO_CHATGPT.zip, if produced
terrain_lod_seam_report.txt, for the C terrain example
OBJ or mesh dump for failing cases
```

## Important non-claims

The public package claims an independent 0BSD Transvoxel-style core candidate.
The full repository separately proves an exact semantic path whose
selection-bearing data is MIT.

It does not claim:

```text
byte/table identity with Eric Lengyel's MIT Transvoxel.cpp
official 73-equivalence-class mapping
finished game terrain visual quality
collision, streaming, materials, gameplay, or performance certification
```

M24-M26 prove the isolated MIT exact semantic path. Official numeric class IDs
and byte identity remain `NOT_PROVEN`. M27 proves
that the same exact selection data cannot be released as 0BSD under the current
provenance policy. The public 0BSD core matches tested boundaries but differs
in interior connectivity for 170/256 regular and 373/512 transition cases.
