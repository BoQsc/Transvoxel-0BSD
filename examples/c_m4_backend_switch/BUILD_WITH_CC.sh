#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../.."
cc -std=c99 -Wall -Wextra -pedantic -Iinclude -Igenerated \
  src/transvoxel.c \
  src/transvoxel_m4_candidate.c \
  src/transvoxel_m4_backend.c \
  examples/c_m4_backend_switch/main.c \
  -o c_m4_backend_switch
./c_m4_backend_switch
