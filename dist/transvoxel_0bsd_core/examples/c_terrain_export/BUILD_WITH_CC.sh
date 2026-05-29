#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
cc -std=c99 -Iinclude -Igenerated src/transvoxel.c examples/c_terrain_export/main.c -o examples/c_terrain_export/terrain_export
examples/c_terrain_export/terrain_export
