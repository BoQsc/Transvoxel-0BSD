#!/bin/sh
cd "$(dirname "$0")/../.." || exit 1
CC=${CC:-cc}
mkdir -p build
$CC -std=c99 -Wall -Wextra -pedantic -Iinclude -Igenerated src/transvoxel.c examples/c_minimal/main.c -o build/c_minimal || exit 1
exec build/c_minimal
