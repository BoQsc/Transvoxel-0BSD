@echo off
setlocal
cd /d "%~dp0\..\.."
zig cc -std=c99 -Iinclude -Igenerated src\transvoxel.c examples\c_terrain_export\main.c -o examples\c_terrain_export\terrain_export.exe
if errorlevel 1 exit /b 1
examples\c_terrain_export\terrain_export.exe
